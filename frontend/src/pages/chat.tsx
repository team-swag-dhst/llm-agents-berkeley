// @ts-nocheck
import { useState } from "react";
import ChatBot, { Button, useMessages } from "react-chatbotify";
import {
  sourceTajMahalImage,
  sourceTajMahalImage2,
  sourceTajMahalImage3,
} from "../mock/images";
import * as _ from "lodash";
import { processSamImage } from "../services.ts/sam-process";
export const Chat = () => {
  const [name, setName] = useState("");
  const [base64IMG, setBase64IMG] = useState("");
  const [clicks, setClicks] = useState([]);
  const mockImagesList = [sourceTajMahalImage2];
  const [processedImg, setProcessedImg] = useState(sourceTajMahalImage);

  const [isLoading, setisLoading] = useState(false);
  const { messages, removeMessage, injectMessage, replaceMessages } =
    useMessages();
  const replaceMessageAfterClick = () => {};
  const convertToBase64 = (selectedFile) => {
    const reader = new FileReader();

    reader.readAsDataURL(selectedFile);

    reader.onload = () => {
      console.log("called: ", reader);
      console.log("base64 img result", reader.result);
      setBase64IMG(reader.result);
    };
  };
  const handleUpload = (params: any) => {
    const files = params.files;
    console.log("Selected Files", files);
    convertToBase64(files[0]);
    // handle files logic here
  };
  const flow = {
    start: {
      message: "Hello there! What is your name?",
      function: (params) => setName(params.userInput),
      path: "upload_image",
    },
    upload_image: {
      message: (params) =>
        `Nice to meet you ${params.userInput}, please upload the photo.`,
      chatDisabled: true,
      file: (params) => handleUpload(params),
      path: "processing",
    },
    reupload_image: {
      message: (params) => `Hi again ${name}, please upload the photo.`,
      chatDisabled: true,
      file: (params) => handleUpload(params),
      path: "end",
    },
    end: {
      transition: () => {
        return;
      },
      message: (params) => {
        setisLoading(true);
        setTimeout(() => {
          setProcessedImg(
            mockImagesList[_.random(0, mockImagesList.length - 1, false)]
          );
          setisLoading(false);
        }, 5000);
        return `Your photo is being processed pls. wait. (${params.userInput}) We will get back to you shortly!`;
      },
      options: ["showImage"],
      path: "showImage",
      chatDisabled: false,
    },
    processing: {
      message: "Your photo is being processed , Pls. wait ...",
      options: ["showImage"],
      chatDisabled: true,
      path: (params) => {
        setTimeout(async () => {
          setProcessedImg(
            mockImagesList[_.random(0, mockImagesList.length - 1, false)]
          );
          setisLoading(false);
          // await params.goToPath('showImage');
        }, 2000);
        return "showImage";
      },
    },
    showImage: {
      message: (params) => {
        console.log("showImage", { params, isLoading });
        if (isLoading) {
          return "Your input is being processed , Pls. wait ...";
        } else {
          return "Request Processed. Based on your request, the following are the suggestions from the Model";
        }
      },
      component: (params) =>
        !isLoading ? (
          <div
            style={{
              padding: "0.25rem",
              border: "solid 2px black",
              marginTop: 10,
              marginLeft: 20,
              maxHeight: "40vh",
              maxWidth: "70vw",
              display: "flex",
              justifyContent: "center",
              height: "auto",
            }}
          >
            <img
              src={`${processedImg}`}
              style={{ maxHeight: "100%", maxWidth: "100%" }}
              onClick={async (event) => {
                await params.injectMessage(
                  `Your request is accepted pls. wait, clicked positions [${
                    event?.nativeEvent?.offsetX || ""
                  },${event?.nativeEvent?.offsetY || ""}] `
                );
                const newBase64Img = await processSamImage(
                  processedImg,
                  [clicks,event].map((e) => [
                    e.nativeEvent?.offsetX, e?.nativeEvent?.offsetY
                  ])
                );
                setProcessedImg(newBase64Img);
                setClicks((clickValues) => [...clickValues, event]);
                console.log("Click listener", { event });
                console.log("clicked params", params);
                
                setTimeout(async () => {
                  setProcessedImg(
                    mockImagesList[
                      _.random(0, mockImagesList.length - 1, false)
                    ]
                  );
                  setisLoading(false);
                  await params.goToPath("showImage");
                }, 2000);
              }}
            />
            {/* {clicks.map((click) => (
            <div
              style={{
                borderRadius: "50%",
                width: "2rem",
                color: "red",
                fill: "red",
                offsetLeft: click.target.offsetLeft,
                offsetTop: click.target.offsetTop,
              }}
            >
              &nbsp;
            </div>
          ))} */}
          </div>
        ) : undefined,
      options: [
        // "reupload_image",
        "showImage",
        "end",
      ],
      path: (params) => {
        // if(params.userInput==='showImage'){

        return isLoading ? "showImage" : "end";
        // }
        // else {
        //   return params.userInput
        // }
      },
    },
    // thank: {
    //   message: async (params: any) => {
    //     await params.injectMessage("I am an injected message!");

    //     return "I am a return message!";
    //   },
    //   path: "start",
    // },
  };
  const styles = {
    headerStyle: {
      background: "#42b0c5",
      color: "#ffffff",
      padding: "10px",
    },
    chatWindowStyle: {
      width: "100%",
      height: "90vh",
    },
    // ...other styles
  };
  // const themes = [{ id: "omen", version: "0.1.0" }];
  const settings = {
    general: { embedded: true },
    chatHistory: { storageKey: "example_simulation_stream" },
    botBubble: { simStream: true },
    header: {
      title: (
        <div
        // style={{cursor: "pointer", margin: 0, fontSize: 20, fontWeight: "bold"}} onClick={
        // 	() => window.open("https://github.com/tjtanjin/")
        // }
        >
          Team Swag
        </div>
      ),
      showAvatar: true,
      // avatar: botAvatar,
      buttons: [
        Button.NOTIFICATION_BUTTON,
        Button.AUDIO_BUTTON,
        Button.CLOSE_CHAT_BUTTON,
      ],
      // closeChatIcon: CloseChatIcon,
    },
  };

  console.log("Changes", { flow, clicks, messages });
  return (
    <div style={{ padding: "2rem" }}>
      <ChatBot
        settings={settings}
        // themes={themes}
        styles={styles}
        flow={flow}
      />
    </div>
  );
};
