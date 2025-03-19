
from agentUMLDiagramGenerator import AgentUMLDiagramGenerator

agent = AgentUMLDiagramGenerator(architectType="macroedit")

conversation = [
    {
        "role": "assistant",
        "content": "Hello I'm Belva Developer! What do you need for your software architect needs today?",
    },
    {
        "role": "user",
        "content": "I need a simple activity diagram for user authentication flow on e-commerce platform"
            },
	{	"role":"assistant",
		"content":"Great! I'll get the diagram and the code ready for you. What coding language do you want to use?"
	},
	{
		"role":"user", 
		"content":"Python"
	}
]


editUMLDiagram = {
    "node": [
        {
            "id": "abc124b4-30cd-4ced-9b43-6ca5bf001c94",
            "position": {
              "x": 100,
              "y": 50
            },
            "data": {
              "name": "Start",
              "node": {
                "id": "abc124b4-30cd-4ced-9b43-6ca5bf001c94",
                "outgoing": [
                  "bbc124b4-30cd-4ced-9b43-6ca5bf001c76"
                ]
              },
              "desc": "The starting point of the authentication flow.",
              "type": "start",
              "altered": "false",
              "filepath": "",
              "createdAt": "2025-03-18T13:48:21.776620",
              "updatedAt": "2025-03-18T13:48:21.776620"
            }
          },
    ],
    "connection": [],
    "codingLanguage": "",
    "completionTokens": 2400,
    "promptTokens": 5000,
}

fullUMLDiagram = {
    "node": [
        {
            "id": "abc124b4-30cd-4ced-9b43-6ca5bf001c94",
            "position": {
              "x": 100,
              "y": 50
            },
            "data": {
              "name": "Start",
              "node": {
                "id": "abc124b4-30cd-4ced-9b43-6ca5bf001c94",
                "outgoing": [
                  "bbc124b4-30cd-4ced-9b43-6ca5bf001c76"
                ]
              },
              "desc": "The starting point of the authentication flow.",
              "type": "start",
              "altered": 'false',
              "filepath": "",
              "createdAt": "2025-03-18T13:48:21.776620",
              "updatedAt": "2025-03-18T13:48:21.776620"
            }
          }
    ],
    "connection": [],
    "codingLanguage": "",
    "completionTokens": 2400,
    "promptTokens": 5000,
}

result = agent.generateUMLDiagram(
    conversation=conversation, editUMLDiagram=editUMLDiagram, fullUMLDiagram=fullUMLDiagram,process=None
)

print(result)
