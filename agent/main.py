import asyncio
import os 
import json
import fitz  # PyMuPDF
from datetime import datetime
from typing import AsyncIterable, Optional

from dotenv import load_dotenv
from google.adk.runners import Runner  
from google.adk.sessions import DatabaseSessionService
from google.adk.agents.run_config import RunConfig
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.events.event import Event
from google.genai import types

from pathlib import Path
from manager.agent import root_agent

load_dotenv()

db_url = "sqlite:///./my_agent_data.db"
session_service = DatabaseSessionService(db_url=db_url)

# Track pending binary messages
class BinaryMessageTracker:
    def __init__(self):
        self.pending_metadata: Optional[dict] = None
        
    def set_metadata(self, metadata: dict):
        self.pending_metadata = metadata
        
    def get_and_clear_metadata(self) -> Optional[dict]:
        metadata = self.pending_metadata
        self.pending_metadata = None
        return metadata

async def start_agent_session(email_id, is_audio=False):
    """Starts an agent session"""
    APP_NAME = "HealthManagerAgent"
    initial_state = {"user_id": email_id}
    session = await session_service.create_session(
        app_name=APP_NAME, user_id=email_id, state=initial_state
    )
    runner = Runner(
        agent=root_agent, app_name=APP_NAME, session_service=session_service
    )
    modality = "AUDIO" if is_audio else "TEXT"
    speech_config = types.SpeechConfig(
        language_code="hi-IN",
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
        ),
    )
    config = {"response_modalities": [modality], "speech_config": speech_config}
    if is_audio:
        config["output_audio_transcription"] = {}
    run_config = RunConfig(**config)
    live_request_queue = LiveRequestQueue()
    live_events = runner.run_live(
        session=session, live_request_queue=live_request_queue, run_config=run_config
    )
    return live_events, live_request_queue
    
async def agent_to_client_messaging(
    websocket: WebSocket, live_events: AsyncIterable[Event]
):
    """Agent to client communication"""
    while True:
        try:
            async for event in live_events:
                if event is None:
                    continue
                if event.turn_complete or event.interrupted:
                    message = {
                        "turn_complete": event.turn_complete,
                        "interrupted": event.interrupted,
                    }
                    await websocket.send_text(json.dumps(message))
                    print(f"[AGENT TO CLIENT]: {message}")
                    continue
                part = event.content and event.content.parts and event.content.parts[0]
                if not part or not isinstance(part, types.Part):
                    continue
                if part.text and event.partial:
                    message = {
                        "type": "text", "mime_type": "text/plain", "data": part.text, "role": "model"
                    }
                    await websocket.send_text(json.dumps(message))
                    print(f"[AGENT TO CLIENT]: text/plain: {part.text}")
                is_audio = (
                    part.inline_data
                    and part.inline_data.mime_type
                    and part.inline_data.mime_type.startswith("audio/pcm")
                )
                if is_audio:
                    audio_data = part.inline_data and part.inline_data.data
                    if audio_data:
                        metadata = {"type": "binary", "mime_type": "audio/pcm", "role": "model"}
                        await websocket.send_text(json.dumps(metadata))
                        await websocket.send_bytes(audio_data)
                        print(f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes.")
        except WebSocketDisconnect:
            print("Client disconnected from agent_to_client_messaging")
            break
        except Exception as e:
            print(f"Error in agent_to_client_messaging: {e}")
            break

async def client_to_agent_messaging(
    websocket: WebSocket, live_request_queue: LiveRequestQueue
):
    """Client to agent communication"""
    binary_tracker = BinaryMessageTracker()
    
    while True:
        try:
            message = await websocket.receive()
            
            if message.get("text"):
                parsed_message = json.loads(message["text"])
                if parsed_message.get("type") == "text":
                    data = parsed_message["data"]
                    role = parsed_message.get("role", "user")
                    content = types.Content(role=role, parts=[types.Part(text=data)])
                    live_request_queue.send_content(content=content)
                    print(f"[CLIENT TO AGENT]: text: {data}")
                elif parsed_message.get("type") == "binary":
                    binary_tracker.set_metadata(parsed_message)
                    print(f"[CLIENT TO AGENT]: Binary metadata received: {parsed_message}")

            elif message.get("bytes"):
                binary_data = message["bytes"]
                metadata = binary_tracker.get_and_clear_metadata()
                
                if metadata:
                    mime_type = metadata["mime_type"]
                    role = metadata.get("role", "user")
                    
                    if mime_type == "audio/pcm":
                        live_request_queue.send_realtime(
                            types.Blob(data=binary_data, mime_type=mime_type)
                        )
                        print(f"[CLIENT TO AGENT]: audio/pcm: {len(binary_data)} bytes")

                    elif mime_type == "application/pdf":
                        filename = metadata.get("filename", "uploaded.pdf")
                        print(f"[CLIENT TO AGENT]: Received PDF '{filename}'. Extracting text...")
                        
                        try:
                            pdf_document = fitz.open(stream=binary_data, filetype="pdf")
                            extracted_text = "".join(page.get_text() for page in pdf_document)
                            pdf_document.close()

                            context_prompt = (
                                f"The user has uploaded the file '{filename}'. "
                                f"Here is the full text content from that file:\n\n---\n\n"
                                f"{extracted_text}\n\n---\n\n"
                                "Acknowledge that you have received and understood this document. "
                                "Wait for the user's next question about it."
                            )
                            text_part = types.Part(text=context_prompt)
                            content = types.Content(role=role, parts=[text_part])
                            live_request_queue.send_content(content=content)
                            print(f"[CLIENT TO AGENT]: Sent extracted text from '{filename}' to the agent.")
                        
                        except Exception as pdf_error:
                            print(f"Error processing PDF file '{filename}': {pdf_error}")
                            error_message = f"Sorry, I was unable to read the file '{filename}'. It might be corrupted or in an unsupported format."
                            error_part = types.Part(text=error_message)
                            error_content = types.Content(role="model", parts=[error_part])
                            # In a real app, send this error back to the client via a custom message
                    else:
                        print(f"[CLIENT TO AGENT]: Unsupported binary mime type: {mime_type}")
                else:
                    print("[CLIENT TO AGENT]: Received binary data without preceding metadata.")
                    
        except WebSocketDisconnect:
            print("Client disconnected from client_to_agent_messaging")
            break
        except Exception as e:
            print(f"Error in client_to_agent_messaging: {e}")
            import traceback
            traceback.print_exc()
            break
    
app = FastAPI()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    is_audio: str = Query(...),
):
    """Client websocket endpoint"""
    print("Waiting for client connection...")
    await websocket.accept()
    print(f"Client #{session_id} connected, audio mode: {is_audio}")
    try:
        live_events, live_request_queue = await start_agent_session(
            session_id, is_audio == "true"
        )
        print(f"Session started for client #{session_id}")
        agent_to_client_task = asyncio.create_task(
            agent_to_client_messaging(websocket, live_events)
        )
        client_to_agent_task = asyncio.create_task(
            client_to_agent_messaging(websocket, live_request_queue)
        )
        done, pending = await asyncio.wait(
            [agent_to_client_task, client_to_agent_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    except WebSocketDisconnect:
        print(f"Client #{session_id} disconnected")
    except Exception as e:
        print(f"Error in websocket_endpoint for client #{session_id}: {e}")
    finally:
        print(f"Cleaning up connection for client #{session_id}")