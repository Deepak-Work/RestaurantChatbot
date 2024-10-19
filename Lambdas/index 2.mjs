import { LexRuntimeV2Client, RecognizeTextCommand } from "@aws-sdk/client-lex-runtime-v2";
const lexruntime = new LexRuntimeV2Client({ region: "us-east-1" });

export const handler = async (event) => {
  try {
      console.log(event.body)
      // Parse the incoming request body
      const requestBody = JSON.parse(event.body);
      // Extract messages from the request (though we won't use them for now)
      const userMessages = requestBody.messages;
      
      const userMessageText = userMessages[0].unstructured.text;
      
      const lexParams = {
            botId: 'OJNW3YQAE6',             // Replace with your Lex V2 bot ID
            botAliasId: 'RHXZCCNWM3',   // Replace with your Lex V2 alias ID
            localeId: 'en_US',
            text: userMessageText,
            sessionId: 'user123',  
            sessionAttributes: {}
        };
        
      // const lexResponse = await lexruntime.recognizeText(lexParams).promise();
      console.log("RecognizeText")
      const lexCommand = new RecognizeTextCommand(lexParams);
      console.log("Lex Runtime")
      const lexResponse = await lexruntime.send(lexCommand);
      console.log("Runtime Sent")
      console.log(lexResponse)
      // Create a boilerplate response message
      const responseMessage = {
          type: "unstructured",
          unstructured: {
              id: "12345",  // You can generate a unique ID for each message
              text: lexResponse.messages[0].content || "No response from Lex",
              timestamp: new Date().toISOString()  // Current timestamp
          }
      };
      console.log("Lex Response")
      console.log(lexResponse.message)

      // Construct the full BotResponse object
      const responseBody = {
          messages: [responseMessage]  // The response expects an array of messages
      };

      console.log(responseBody)
      // Return the response
      return {
          statusCode: 200,
          body: JSON.stringify(responseBody),
          headers: {
              'Content-Type': 'application/json',
              "Access-Control-Allow-Headers" : "Content-Type",
              "Access-Control-Allow-Origin": "*",
              "Access-Control-Allow-Methods": "OPTIONS,POST"
          }
      };
  } catch (error) {
      // Return an error response in case something goes wrong
      return {
          statusCode: 500,
          body: JSON.stringify({
              code: 500,
              message: "An unexpected error occurred",
            error: error.message
          }),
          headers: {
              'Content-Type': 'application/json',
              "Access-Control-Allow-Headers" : "Content-Type",
              "Access-Control-Allow-Origin": "*",
              "Access-Control-Allow-Methods": "OPTIONS,POST"
          }
      };
  }
};
