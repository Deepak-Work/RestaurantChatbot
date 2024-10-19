import { SQSClient, SendMessageCommand } from "@aws-sdk/client-sqs";

const sqsClient = new SQSClient({ region: 'us-east-1' });

export const handler = async (event) => {
    let response = '';
    console.log("Event received:", JSON.stringify(event));

    const intentName = event?.sessionState?.intent?.name;
    const slots = event?.sessionState?.intent?.slots || {};
    
    console.log(intentName)

    switch (intentName) {
        case 'GreetingIntent':
            response = {
                sessionState: {
                    dialogAction: {
                        type: 'Close',
                        fulfillmentState: 'Fulfilled',
                        message: { contentType: 'PlainText', content: 'Hi there, how can I help?' }
                    },
                    intent: {
                        name: intentName,
                        state: 'Fulfilled'
                    }
                }
            };
            break;

        case 'ThankYouIntent':
            response = {
                sessionState: {
                    dialogAction: {
                        type: 'Close',
                        fulfillmentState: 'Fulfilled',
                        message: { contentType: 'PlainText', content: 'You’re welcome!' }
                    },
                    intent: {
                        name: intentName,
                        state: 'Fulfilled'
                    }
                }
            };
            break;

        case 'DiningSuggestionsIntent':
            const location = slots.Location?.value?.interpretedValue || null;
            const cuisine = slots.Cuisine?.value?.interpretedValue || null;
            const diningTime = slots.DiningTime?.value?.interpretedValue || null;
            const diningDate = slots.DiningDate?.value?.interpretedValue || null;
            const numberOfPeople = slots.NumberOfPeople?.value?.interpretedValue || null;
            const email = slots.Email?.value?.interpretedValue || null;

            if (!location || !cuisine || !numberOfPeople || !diningTime || !diningDate || !email) {
                // One or more slots are still missing, return ElicitSlot for Lex to ask the next question
                const nextSlot = !location ? 'Location' :
                                 !cuisine ? 'Cuisine' :
                                 !numberOfPeople ? 'NumberOfPeople':
                                 !diningTime ? 'DiningTime':
                                 !diningDate ? 'DiningDate' : 
                                 !email ? 'Email' : null;

                console.log(nextSlot)

                response = {
                    sessionState: {
                        dialogAction: {
                            type: 'ElicitSlot',
                            slotToElicit: nextSlot
                        },
                        intent: {
                            name: 'DiningSuggestionsIntent',
                            slots: {
                                Location: { value: { interpretedValue: location }},
                                Cuisine: { value: { interpretedValue: cuisine }},
                                NumberOfPeople: { value: { interpretedValue: numberOfPeople }},
                                DiningTime: { value: { interpretedValue: diningTime }},
                                DiningDate: { value: { interpretedValue: diningDate }},
                                Email: { value: { interpretedValue: email }}
                            }
                        }
                    }
                };
            } else {
                // All slots are filled, proceed to push to SQS
                console.log("Constructing message for SQS with the following details:");
                console.log("Location:", location);
                console.log("Cuisine:", cuisine);
                console.log("Number of People:", numberOfPeople);
                console.log("Dining Time:", diningTime);
                console.log("Dining Date:", diningDate);
                console.log("Email:", email);
                                
                const sqsParams = {
                    MessageBody: JSON.stringify({
                        location,
                        cuisine,
                        numberOfPeople,
                        diningTime,
                        diningDate,
                        email
                    }),
                    QueueUrl: "https://sqs.us-east-1.amazonaws.com/863518439994/Q1"
                };

                try {
                    const sqsCommand = new SendMessageCommand(sqsParams);
                    const response_ = await sqsClient.send(sqsCommand);
                    console.log(response_)
                    console.log("Message added to the queue")

                    // Respond to the user
                    response = {
                        sessionState: {
                            dialogAction: {
                                type: 'Close',
                                fulfillmentState: 'Fulfilled',
                                message: { 
                                    contentType: 'PlainText', 
                                    content: `Thanks for your info! I will notify you with dining suggestions at ${email}.`
                                }
                            },
                            intent: {
                                name: intentName,
                                state: 'Fulfilled'
                            }
                        }
                    };
                } catch (error) {
                    console.error("Error sending message to SQS:", error);
                    response = {
                        sessionState: {
                            dialogAction: {
                                type: 'Close',
                                fulfillmentState: 'Failed',
                                message: { contentType: 'PlainText', content: 'Sorry, something went wrong with your request.' }
                            },
                            intent: {
                                name: intentName,
                                state: 'Fulfilled'
                            }
                        }
                    };
                }
            }
            break;
    }

    return response;
};
