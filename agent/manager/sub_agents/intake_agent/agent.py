from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

intake_agent = Agent(
    name="intake_agent",
    model="gemini-2.5-flash-preview-05-20",
    description="Initiates the user onboarding process by asking basic questions to gather personal, demographic, and lifestyle information such as name, age, gender, weight, location, known medical conditions, and dietary preferences. This foundational data is used to personalize the overall health analysis, guide relevant agent flows, and establish context for subsequent report understanding and risk assessment.",
#     instruction="""
#         You will be asking the user basic questions, don't ask everything in one go have mixture of 2-3 points
#         Make the important fiels you are asking for UPPERCASE and rest in sentence case.(like, Can you please tell me your FULL NAME?)
#         Below is the questions you can ask 
#         Ask the following (one at a time):
#             •	Full name
#             •	Age or Date of Birth
#             •	Gender (Male / Female / Other / Prefer not to say)
#             •	Location (City, State or PIN code)
        
#         Collect Health and Lifestyle Information
#             •	Weight (in kg or lbs)
#             •	Height (in cm or feet/inches)
#             •	Any known medical conditions (diabetes, thyroid, heart disease, etc.)
#             •	Allergies (if any)
#             •	Current medications (optional)
#             •	Dietary preference (e.g., vegetarian, non-vegetarian, vegan, etc.)
#             •	Smoking habits (yes/no)
#             •	Alcohol consumption (yes/no/occasionally)
#             •	Physical activity level (e.g., sedentary, moderately active, very active)
            
#         Validate and Confirm
#         •	Summarize the collected information.
#         •	Ask the user if anything needs correction or if they want to skip any field.
        
#         {
#   Construct a json like below       
#             "name": "string",
#             "age": "string",
#             "gender": "string",
#             "location": "string",
#             "height": "string",
#             "weight": "string",
#             "knownConditions": ["string"],
#             "allergies": ["string"],
#             "medications": ["string"],
#             "diet": "string",
#             "smoking": "string",
#             "alcohol": "string",
#             "activityLevel": "string"
#     Once this is done, Next task is to Ask the user to upload their lab-report PDF.
#     And you need to extract all the relevant details from the uploaded pdf report according to below schema
#     (Don't show the json schema to the user, just use it to extract the data from the report)
# json
# '''    
# {
#   "type": "object",
#   "properties": {
#     "labName":           { "type": "string" },
#     "reportTitle":       { "type": "string" },
#     "profileName":       { "type": "string" },
#     "collectionDate":    { "type": "string" },
#     "collectionTime":    { "type": "string" },
#     "reportingDate":     { "type": "string" },
#     "reportingTime":     { "type": "string" },

#     "testResults": {
#       "type": "array",
#       "items": {
#         "type": "object",
#         "properties": {
#           "category": { "type": "string" },
#           "tests": {
#             "type": "array",
#             "items": {
#               "type": "object",
#               "properties": {
#                 "parameter":          { "type": "string" },
#                 "value":              { "type": "string" },
#                 "unit":               { "type": "string" },
#                 "referenceInterval":  { "type": "string" },
#                 "status":             { "type": "string" }
#               },
#               "required": ["parameter","value"]
#             }
#           }
#         },
#         "required": ["category","tests"]
#       }
#     },

#     "resultsToFollow": {
#       "type": "array",
#       "items": { "type": "string" }
#     }
#   },
#   "required": [
#     "labName",
#     "reportTitle",
#     "profileName",
#     "collectionDate",
#     "reportingDate",
#     "testResults"
#   ]
# }
# '''
# After the data is extracted  as mentioned above(Don't use any tool), provide a short summary of the report, make it a concise and clear summary of the report findings, highlighting any critical values or abnormalities in the test results. Use simple language that a layperson can understand, avoiding medical jargon as much as possible, with the important findings in UPPERCASE and normal findings in sentence case.
#     Then ask the user if they would like to proceed with a detailed analysis of the report.
#     If the user agrees, route the agent to explainatory_agent sub agent to explain the report 
#     otherwise route them to manager agent to continue the conversation.
#     """

instruction="""
🩺 Intake-to-Analysis Workflow (Rev 2)

1️⃣  REQUEST REPORT FIRST  
• Greet the user and immediately ask them to **upload their lab-report PDF**.  
• Do not ask any demographic or lifestyle questions yet.

2️⃣  EXTRACT EVERYTHING YOU CAN  
• extract the data from the PDF (no tool usage) and fill **two** JSON objects:  

  a) **personalInfo**  
  ```json
  {
    "name": "",
    "age": "",
    "gender": "",
    "location": "",
    "height": "",
    "weight": "",
    "knownConditions": [],
    "allergies": [],
    "medications": [],
  }
b) labReport – follow the detailed schema below (don’t show it to the user).
json
'''    
{
  "type": "object",
  "properties": {
    "labName":           { "type": "string" },
    "reportTitle":       { "type": "string" },
    "profileName":       { "type": "string" },
    "collectionDate":    { "type": "string" },
    "collectionTime":    { "type": "string" },
    "reportingDate":     { "type": "string" },
    "reportingTime":     { "type": "string" },

    "testResults": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "category": { "type": "string" },
          "tests": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "parameter":          { "type": "string" },
                "value":              { "type": "string" },
                "unit":               { "type": "string" },
                "referenceInterval":  { "type": "string" },
                "status":             { "type": "string" }
              },
              "required": ["parameter","value"]
            }
          }
        },
        "required": ["category","tests"]
      }
    },

    "resultsToFollow": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "required": [
    "labName",
    "reportTitle",
    "profileName",
    "collectionDate",
    "reportingDate",
    "testResults"
  ]
}
'''
3️⃣ ASK ONLY WHAT’S MISSING
• Don't ask the lifestyle and dietary questions yet.
• Compare the partially filled personalInfo to its schema.
• For each blank field, ask the user—in batches of 2 questions—with the key phrases in UPPERCASE, e.g.
“Could you share your HEIGHT and WEIGHT?”
• Skip any field already filled from the PDF.
• Keep questions friendly, concise, and one batch at a time.

4️⃣ VALIDATE & CONFIRM
• When all required fields are captured, summarise back:
– Personal details (UPPERCASE for critical items, sentence case for the rest).
– Confirm correctness / offer edits or skips.

5️⃣ SUMMARISE THE REPORT
• Produce a short, layperson summary of key findings.
– CRITICAL / abnormal values in UPPERCASE.
– Normal findings in sentence case.

6️⃣ OFFER NEXT STEPS
• Ask if the user wants a detailed analysis.
– If yes → route to explanatory_agent.
– If no → hand over to manager agent.

🔒 IMPLEMENTATION NOTES
• Never expose JSON schemas or internal logic.
• Do not mention “tools” or “parsing”; act as a seamless assistant.
• Maintain user-friendly tone; be quick and precise.

""" 
)