import os
import json
import re
import datetime
import traceback
from uuid import uuid4
from typing import Final, Tuple
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from dotenv import load_dotenv, find_dotenv
import sys

load_dotenv(find_dotenv())

AGENT_CONTROL_MODEL: Final[str] = os.environ.get("AGENT_CONTROL_MODEL_CURRENT")
OPENAI_API_KEY: Final[str] = os.environ.get("OPENAI_API_KEY")
client: Final[OpenAI] = OpenAI(api_key=OPENAI_API_KEY)


class AgentFileParser:
    """
    This class is a task agent that will parse a single file and extract the relevant information needed to generate a class diagram for a single file.

    Variables that will be used and its context in this class:
    1. __model : Indicates the LLM of choice to use - will be a string type - In this case currently on OpenAI
    2. __systemPrompt : prompt that will be used for the LLM - will be a string type
    3. __messages : List of dictionaries with the following key value pairs:
    a. role - Either to be system, user, or assistant.
    b. content - The message passed to OpenAI containing the prompt
    4. __fileStructure: details of the file
    5. __architectType: currently supports edits
    """

    # Model ID of the agent
    __model: str = None

    # Instructions given to the agent
    __systemPrompt: str = None

    # Chat history between the agent
    __messages: list[dict] = None

    # Flag to determine the type of architect this will be - currently only supports 'creation'
    __architectType: str = None

    # File Structure
    __fileStructure: list[dict] = None

    def __init__(self, model: str = None, architectType: str = None):
        self.__model = AGENT_CONTROL_MODEL if model is None else model
        self.__architectType = "creation" if architectType is None else architectType
        self.__systemPrompt = self.__getSystemPrompt()
        self.__messages = [{"role": "system", "content": self.__systemPrompt}]

    def __getSystemPrompt(self) -> str:
        systemPrompt: str = f"""
        You are the best File Parser agent with UML expertise. Identify classes, attributes, operations, relationships, and dependencies from code and format it for UML. Generate UML blocks with additional features like abstract classes and interfaces.

        Inputs include:
        - FileStructure: dictionary with path, filename, desc, language, framework, code.

        Instructions:
        - Extract classes, methods, objects. Include name, type, attributes, operations, and description. Identify interface, abstract classes and data types with stereotypes (<<interface>>, <<abstract>>, <<datatype>>).
        - Capture relationships within classes and objects. For each connection, detail the filepath, name, source, target, role, type, and multiplicity.
        
        Conventions:
        - Use proper UML class notations (capitalized class names, method signatures with visibility).
        - Use stereotypes where necessary. Classes: capital letters (e.g., OAuth2Service). Methods: methodName(params) -> returnType with visibility.
        - Use UML notation for abstract classes and interfaces.
        - Example output should adhere to these guidelines.
        
        Notes and exceptions:
        - Avoid generating connections for standard libraries.
        - Ignore standard libraries for filepath.
        """
        return systemPrompt

    def __createMessage(self, role: str = None, message: str = None) -> dict:
        return {"role": role, "content": message}

    def __runLLM(self, message: list = None) -> Tuple[str, int, int, str]:
        completion: ChatCompletion = client.chat.completions.create(
            model=self.__model,
            messages=message,
            temperature=0.15,
            top_p=1,
            n=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        response: str = completion.choices[0].message.content
        promptTokens: int = completion.usage.prompt_tokens
        completionTokens: int = completion.usage.completion_tokens
        stopReason: str = completion.choices[0].finish_reason
        return response, promptTokens, completionTokens, stopReason

    def __extractUMLContent(self) -> dict:
        response: str = None
        completionTokens: int = None
        promptTokens: int = None
        stopReason: str = None
        finalUMLBlock: str = None
        codeRepo: list[dict] = []
        codeRepo.append(self.__fileStructure)

        codeRepoStructureString = (
            str(codeRepo) if codeRepo else None
        )

        prependMsg: str = f"""
        ==============
        FILE STRUCTURE
        =============
        {codeRepoStructureString}

        Remember: You are the best UML generator. Follow all instructions carefully.
        """
        self.__messages.append(self.__createMessage(role="user", message=prependMsg))

        isFinished = False
        diagramIteration = 0
        totalCompletionTokens: int = 0
        totalPromptTokens: int = 0

        while not isFinished and diagramIteration <= self.__maxIterations:
            diagramIteration += 1
            try:
                response, promptTokens, completionTokens, stopReason = self.__runLLM(self.__messages)
                finalUMLBlock = response if diagramIteration == 1 else finalUMLBlock + response
                totalCompletionTokens += completionTokens
                totalPromptTokens += promptTokens

                self.__messages.append({"role": "assistant", "content": response})

                if stopReason == "stop":
                    break
                elif diagramIteration > self.__maxIterations:
                    break
                else:
                    self.__messages.append(
                        {
                            "role": "user",
                            "content": f"Continue from where you left off. Here are the last 20 characters of the last response: {response[-20:]}",
                        }
                    )
            except Exception as error:
                traceback.print_exc()
                return None

        try:
            jsonMatch = re.search("```json\n(.*?)\n```", finalUMLBlock, re.DOTALL)
            if jsonMatch:
                responseUse = jsonMatch.group(1)
                trimmedResponse = json.loads(responseUse)

                nodes = trimmedResponse.get("node", [])
                for nodeBlock in nodes:
                    nodeBlock["filepath"] = self.__fileStructure.get("path", "")

                connections = trimmedResponse.get("connection", [])
                for connectionBlock in connections:
                    pass  # Further processing if needed

                diagramResponse = trimmedResponse
                diagramResponse["promptTokens"] = totalPromptTokens
                diagramResponse["completionTokens"] = totalCompletionTokens
                return diagramResponse
            else:
                raise ValueError(
                    "Invalid JSON format or missing '```json' block in the input string."
                )

        except (
            json.decoder.JSONDecodeError,
            AttributeError,
            KeyError,
            ValueError,
        ) as jsonError:
            print(jsonError)
            return None

    def __uuidMapper(self, result: dict = None) -> dict:
        uuidMapper: dict = {}
        for newBlock in result["node"]:
            uuidMapper[newBlock["id"]] = str(uuid4())
            newBlock["id"] = uuidMapper[newBlock["id"]]
        return result

    def generateUMLBlock(
        self, fileStructure: dict = None, maxIterations: int = None, retries: int = None
    ) -> dict:
        retries = 5 if retries is None else retries
        self.__fileStructure = fileStructure
        self.__maxIterations = maxIterations
        result: dict = None

        for attempt in range(retries):
            try:
                result = self.__extractUMLContent()
                if result is not None:
                    uuidModifiedResult = self.__uuidMapper(result=result)
                    return uuidModifiedResult
            except Exception as e:
                print(e)