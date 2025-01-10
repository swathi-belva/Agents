import json
import os
import re
import traceback
from typing import Final, Tuple, Set
from datetime import datetime

from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion
from commonUtils.logger.logger import getLogger

logger = getLogger()

# Environment declarations
AGENT_CONTROL_MODEL: Final[str] = os.environ.get("AGENT_CONTROL_MODEL_CURRENT")
OPENAI_API_KEY: Final[str] = os.environ.get("OPENAI_API_KEY")
client: Final[OpenAI] = OpenAI(api_key=OPENAI_API_KEY)


class AgentRecommendations:
    """
    This class is a task agent that will generate recommendations.

    Variables that will be used and its context in this class:
    1. __model : Indicates the LLM of choice to use - will be a string type - In this case currently on OpenAI
    2. __systemPrompt : prompt that will be used for the LLM - will be a string type
    3. __messages : List of dictionaries with the following key value pairs:
    a. role - Either to be system, user, or assistant.
    b. content - The message passed to OpenAI containing the prompt
    4. __sweType : currently supports 'creation'
    5. __umlStructure: UML structure in JSON format.
    6. __scanResult: Scan result for each node.
    7. __dateTime: DateTime in string format.
    """

    # Model ID of the agent
    __model: str = None

    # Instructions given to the agent
    __systemPrompt: str = None

    # Chat history between the agent
    __messages: list[dict] = None

    # Software Engineer Type: Supports 'creation'
    __sweType: str = None

    # UML Structure
    __umlStructure: dict = None

    # Scan Results
    __scanResult: dict = None

    # Current date and time
    __dateTime: str = None

    def __init__(self, model: str = None, sweType: str = None):
        """
        Initializes the class

        Inputs -
        1. model: Indicates the LLM of choice to use - will be a string type - In this case currently on OpenAI
        2. sweType: Supports 'creation' and 'edit' - default is 'creation'
        """

        # Getting the current date and time
        self.__dateTime = str(datetime.now())

        # Variable declarations
        self.__model = AGENT_CONTROL_MODEL if model is None else model
        self.__sweType = "creation" if sweType is None else sweType

        # Generate the system prompts and messages objects
        self.__systemPrompt = self.__getSystemPrompt()

        self.__messages = [
            self.__createMessage(role="system", message=self.__systemPrompt)
        ]

    def __getSystemPrompt(self) -> str:
        """
        Generates the system prompt.

        Input -
        None: Uses the class object

        Output -
        systemPrompt: A string that resembles the system prompt.

        """
        if "creation" in self.__sweType:
            systemPrompt: str = (
                """
                You are tasked with generating vulnerability assessment recommendations for a set of UML nodes based on a scan result. For each node, 
                assess the severity of identified vulnerabilities and provide specific recommendations for remediation where necessary.
                You will be given the following input:
                1.nodeStructure: A dictionary describing the properties of each UML node, such as:
                    -id: Unique identifier.
                    -name: Name of the node.
                    -attribute: List of node attributes.
                    -operation: List of operations/methods of the node.
                    -desc: Description of the node.
                    -type: Type of UML block (e.g., Class, Interface).
                    -position: X and Y coordinates of the node.
                    -createdAt: Date and time when the node was created.
                    -updatedAt: Date and time when the node was last updated.
                    -altered: Boolean flag indicating whether the node requires code modification.
                    -filepath: Path to the file containing this node's definition.
                    -codingLanguage: The coding language associated with the node (if available).
                    connections: A list of connections between nodes. Each connection dictionary has the following properties:
                        -connectionId: A unique identifier for the connection.
                        -source: ID of the source node.
                        -target: ID of the target node.
                        -role: Contextual description of the relationship (optional).
                        -type: Type of relationship (e.g., association, inheritance, composition).
                        -multiplicity: Describes the relationship multiplicity using UML notation.

                2.scanResults: A list of dictionaries that contain the scan results.
                Each dictionary represents a node with detailed properties about the node and its associated vulnerabilities.
                Each node dictionary has the following properties:
                    -id: A unique identifier for the node.
                    -name: Name of the node.
                    -severity: Severity level of each node. 
                    -summary: Summary of the scan result and its impact on each node.
                    If the analysisType is 'vulnerability',Possible values are:
                        none: No vulnerabilities detected, all systems are functioning as expected.
                        low: Low-level vulnerabilities. These vulnerabilities are unlikely to have immediate severe impacts but should be addressed eventually.
                        medium: Medium-level vulnerabilities. These require attention but are not critical. They might lead to issues under specific conditions.
                        high: High-level vulnerabilities. These are critical vulnerabilities and should be addressed immediately.
                =============
                INSTRUCTIONS:
                =============
                1. For each node, Assess the severity of the scan.
                2. Based on the severity, generate an appropriate recommendationSummary.
                3. Determine if a recommendation is necessary based on the given severity.If severity is None, do not generate any recommendation for that node.
                4. You need to provide a detailed recommendation by analyzing the node structure and scan summary for each node given.
                5. Always make sure recommendations provided should be based on UML nomenclature.
                6. You need to analyse the scan results and generate the appropriate recommendations. Scan results would be related to any of the following:
                   - Vulnerability
                   - Security
                   - Compliance
                   - Infrastructure
                    
                7. Your task is to generate a list of recommendations based on the scan result for each node in the system. Each node dictionary in the output will 
                   include:
                    -id: The remapped unique identifier for the node.
                    -name: Name of the node.
                    -recommendation: Boolean flag indicating whether a recommendation is needed (True for recommendation needed, False if no recommendation is necessary).
                    -recommendationSummary: A brief 2-3 sentence description of the recommendation. If no action is required, state "No recommendations needed."
                    -recommendationDate: Date and time when the recommendation was made.
                ==============    
                Example Output
                ==============
                [
                    {{
                    "name": "User Authentication",
                    "recommendation": true,
                    "recommendationSummary": "Add stereotypes to methods indicating they handle sensitive data (e.g., <<sensitive>> for authenticate and send2FACode). Include a note highlighting the need for encryption in storing phone numbers and proper error handling annotations for failed authentications
                    }}
                ]
                Notes: 
                1. Do not generate any explanations and comments in the response.
                """.format(
                    dateTime=self.__dateTime
                )
            )
        return systemPrompt

    def __runLLM(self, message: list = None) -> Tuple[str, int, int]:
        """
        Runs the LLM with a list of messages.

        Input -
        message: A list of messages to run.

        Outputs -
        1. response: String from the response of the LLM
        2. promptTokens: Integer that tells us the number of tokens used for the prompt
        3. completionTokens: Integer that tells us the number of tokens used to generate the response
        """

        # Call the LLM to return a response
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

        return response, promptTokens, completionTokens

    def __createMessage(self, role: str = None, message: str = None) -> dict:
        """
        Creates prepend messages prior to running the LLMs.

        Inputs -

        1. role: A string indicating either "system", "user", or "assistant".
        2. message: A string ready to be appended to the messages list.

        Output -
        addedMessage: A dictionary that contains the prepend message with the user.
        """

        addedMessage: dict = {"role": role, "content": message}
        return addedMessage

    def __getRecommendations(self) -> dict:
        """
        This function validates the code generated based on the UML structure and code as inputs.
        It will provide an array of JSON objects for which the keys are "result" (dict),"passing" (boolean) and "reason" (string) for each file.

        Inputs -
        None

        Output -
        a.result: validation result having the following keys:
            -id: The remapped unique identifier for the node.
            -name: Name of the node.
            -recommendation: boolean value indicating whether recommendation is required.
            -recommendationSummary: recommendation summary based on the scan result.
            -recommendationDate: Date and time when the recommendation was made.
        b. promptTokens: integer indicating the number of tokens that were fed into OpenAI
        c. completionTokens: integer indicating the number of tokens generated by OpenAI
        """
        # Variable declarations:
        response: str = None
        promptTokens: int = None
        completionTokens: int = None
        uml: list[dict] = []
        umlDict: dict = None
        umlStructureString: str = None
        connectionList: list[dict] = []
        connectionDict: dict = None
        connectionStructureString: str = None
        scanList: list[dict] = []
        scanDict: dict = None
        scanStructureString: str = None
        cleanedResponse: str = None
        analysisType: str = None
        recommendationSummary: dict = None

        # Building the dictionaries and if there is an empty dictionary we will use None for any of the inputs.
        if self.__sweType == "creation":
            try:
                # Ensure self.__umlStructure["node"] exists and is iterable (like a list)
                if "node" not in self.__umlStructure:
                    raise KeyError('"node" key is missing in __umlStructure')

                if not isinstance(self.__umlStructure["node"], list):
                    raise TypeError("Expected self.__umlStructure to be a list.")

                for info in self.__umlStructure["node"]:
                    umlDict = dict()
                    umlDict["id"] = info.get("id", "")
                    umlDict["name"] = info.get("name", "")
                    umlDict["attribute"] = info.get("attribute", "")
                    umlDict["desc"] = info.get("desc", "")
                    umlDict["operation"] = info.get("operation", "")
                    umlDict["type"] = info.get("type", "")
                    uml.append(umlDict)
                uml.append({"codingLanguage": self.__umlStructure["codingLanguage"]})

            except KeyError as e:
                umlStructureString = None
            except TypeError:
                umlStructureString = None

            umlStructureString = str(uml) if uml else None  # checks if uml is empty

            try:
                # Ensure self.__umlStructure["connection"] exists and is iterable (like a list)
                if not isinstance(self.__umlStructure.get("connection"), list):
                    raise TypeError("Expected 'connection' to be a list.")

                for connection in self.__umlStructure["connection"]:
                    connectionDict = dict()
                    connectionDict["connectionId"] = connection.get("connectionId", "")
                    connectionDict["source"] = connection.get("source", "")
                    connectionDict["target"] = connection.get("target", "")
                    connectionDict["role"] = connection.get("role", "")
                    connectionDict["type"] = connection.get("type", "")
                    connectionDict["multiplicity"] = connection.get("multiplicity", "")
                    connectionList.append(connectionDict)

            except KeyError as e:
                connectionStructureString = None

            except TypeError:
                connectionStructureString = None

            # Assign the connectionStructureString based on whether connectionList is empty or not
            connectionStructureString = str(connectionList) if connectionList else None

            try:
                # Ensure self.__scanResult["result"] exists and is iterable (like a list)
                if not isinstance(self.__scanResult.get("result"), list):
                    raise TypeError("Expected 'result' to be a list.")

                analysisType = self.__scanResult.get("analysisType")

                for scan in self.__scanResult["result"]:
                    scanDict = dict()
                    scanDict["id"] = scan.get("id", "")
                    scanDict["name"] = scan.get("name", "")
                    if analysisType == "vulnerability":
                        scanDict["vulnerabilitySeverity"] = scan.get(
                            "vulnerabilitySeverity", ""
                        )
                        scanDict["vulnerabilitySummary"] = scan.get(
                            "vulnerabilitySummary", ""
                        )
                    scanList.append(scanDict)

            except KeyError:
                scanStructureString = None

            except TypeError:
                scanStructureString = None

            # Convert code to a string, or set it to None if it's empty
            scanStructureString = str(scanList) if scanList else None

        # Adding a system prepend
        if "creation" in self.__sweType:
            prependMsg: str = (
                """
                Here's the UML content:
                {umlStructureString}

                Here's the connection string:
                {connectionStructureString}

                Here's the scan summary generated for every node:
                {scanStructureString}

                """.format(
                    umlStructureString=umlStructureString,
                    connectionStructureString=connectionStructureString,
                    scanStructureString=scanStructureString,
                )
            )
        logger.info(
            f"Prepend message for Recommendations Agent is the following: {prependMsg}"
        )

        # Add user message to list
        self.__messages.append(self.__createMessage(role="user", message=prependMsg))
        # Runs the LLM and returns back a typed dict which are the results of the full stack code review.
        try:
            logger.info(
                "About to call OpenAI for Recommendations Agent for code validation."
            )
            response, promptTokens, completionTokens = self.__runLLM(self.__messages)
            logger.info(
                "Finished calling OpenAI for Recommendations agent for code validation."
            )
            try:
                result = re.sub(r"```json\n|```", "", response)
                cleanedResponse = json.loads(result)
                # Add current time to each dictionary in the cleanedResponse list
                if isinstance(cleanedResponse, list):
                    currentTime: str = str(datetime.now())
                    for node in cleanedResponse:
                        if isinstance(node, dict):
                            if node["recommendation"]:
                                node["recommendationDate"] = currentTime

                try:
                    recommendationSummary = {
                        "result": cleanedResponse,
                        "promptTokens": promptTokens,
                        "completionTokens": completionTokens,
                    }
                    return recommendationSummary
                except KeyError as keyError:
                    logger.error("Missing key in cleanedResponse: %s", keyError)
                    traceback.print_exc()
            except json.decoder.JSONDecodeError as jsonError:
                logger.error(
                    "JSON conversion error %s for %s", jsonError, cleanedResponse
                )
                traceback.print_exc()
        except Exception as error:
            logger.error("Recommendations Agent Msg Error: %s", error)
            traceback.print_exc()

    def generateRecommendations(
        self,
        umlStructure: dict = None,
        scanResult: dict = None,
        retries: int = None,
    ) -> dict:
        """
        Inputs -
        1. umlStructure:
        node:
            a)id: Unique identifier of the class/component.
            b)name: Name of the component/service
            c)attribute: Variables that belong to the class.
            d)operation: functions or methods in the class
            e)desc: a brief description of the component and its functionality.
            f)type: A string that is the type of UML block for that given block (e.g. class)
        connection: A list of dictionaries containing the following keys -
            a. connectionId: A unique identifier for a particular connection between two classes.
            b. source: The classId of the origin class
            c. target: The classId of the destination class
            d. role: Optional context phrases within the connection.
            e. type: The type of the connection
            f. multiplicity: dictionary containing the following keys -
                i. source: multiplicity describing the connection for the source
                ii. target: multiplicity describing the connection for the target
        2. scanResult:Each dictionary represents a node with detailed properties about the node and its associated vulnerabilities.
            Each node dictionary has the following properties:
                -id: A unique identifier for the node.
                -name: Name of the node for reference.
                -severity: Severity level of the identified vulnerabilities
                -summary: Summary of the scan result.
                -scanDate: Scan date of the vulnerability.
            analysisType: Type of tha analysis(ex: vulnerability, infrastructure, security, compliance)
        3. retries: Integer tells us the maximum number of retries allowed for running through the LLM.

        Output -
        a.result: validation result having the following keys:
            -id: The remapped unique identifier for the node.
            -name: Name of the node.
            -recommendation: boolean value indicating whether recommendation is required.
            -recommendationSummary: recommendation summary based on the scan result.
            -recommendationDate: Date and time when the recommendation was made.
        b. promptTokens: integer indicating the number of tokens that were fed into OpenAI
        c. completionTokens: integer indicating the number of tokens generated by OpenAI
        """
        # Variable declarations
        recommendationSummary: dict = None
        retries = 5 if retries is None else retries
        self.__umlStructure = umlStructure
        self.__scanResult = scanResult

        # Main retry loop
        for attempt in range(retries):
            try:
                recommendationSummary = self.__getRecommendations()
                if self.__sweType == "creation":
                    requiredKeys: list[str] = [
                        "name",
                        "recommendation",
                        "recommendationSummary",
                        "recommendationDate",
                    ]
                if recommendationSummary is not None:
                    # Check for missing keys
                    if self.__sweType == "creation":
                        missingKeys: Set[str] = {
                            key
                            for entry in recommendationSummary.get("result", [])
                            for key in requiredKeys
                            if key not in entry
                        }
                    if not missingKeys:
                        # Iterate over each node in recommendationSummary and map the id from scanResult based on the name
                        for i, node in enumerate(recommendationSummary['result']):
                            # Directly assign the 'id' from scanResult based on index
                            node['id'] = self.__scanResult['result'][i]['id']
                        return recommendationSummary
                else:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                    traceback.print_exc()
            except Exception as e:
                logger.error(f"Unexpected error during attempt {attempt + 1}: {str(e)}")
                traceback.print_exc()
                if attempt == retries - 1:
                    logger.error(f"Ran out of retries {attempt + 1}: {str(e)}")
                    traceback.print_exc()
