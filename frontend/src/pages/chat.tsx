// @ts-nocheck
import { useState } from "react";
import ChatBot, { Button, useFlow, useMessages } from "react-chatbotify";
import {
  sourceTajMahalImage,
  sourceTajMahalImage2,
  sourceTajMahalImage3,
} from "../mock/images";
import * as _ from "lodash";
import { processSamImage } from "../services.ts/sam-process";
import { tourguide } from "../services.ts/tourguide";
import { GpsLocation } from "../components/GPSLocation";

export const Chat = () => {
  const [name, setName] = useState("");
  const [base64IMG, setBase64IMG] = useState("");
  const [recentResponse, setRecentResponse] = useState("");

  const [geoData, setGeoData] = useState({
    loading: false,
    error: false,
    latitude: 0,
    longitude: 0,
  });
  const [clicks, setClicks] = useState([]);
  const mockImagesList = [sourceTajMahalImage2];
  const [processedImg, setProcessedImg] = useState("");

  const [fetchingLocation, setFetchingLocation] = useState(false);
  const [isLoading, setisLoading] = useState(false);
  const { messages, removeMessage, injectMessage, replaceMessages } =
    useMessages();
  const { restartFlow } = useFlow();
  const replaceMessageAfterClick = () => {};
  const convertToBase64 = (selectedFile) => {
    const reader = new FileReader();

    reader.readAsDataURL(selectedFile);

    reader.onload = () => {
      // console.log("called: ", reader);
      // console.log("base64 img result", reader.result);
      setBase64IMG(reader.result);
      setProcessedImg(reader.result);
    };
  };
  const handleUpload = (params: any) => {
    const files = params.files;
    // console.log("Selected Files", files);
    convertToBase64(files[0]);
    // handle files logic here
  };
  // const getCurrentLocation = (geoData)=>{
  //   if (geoData.loading) {
  //     console.log('still Loading ...')
  //   }

  //   if (geoData.error) {
  //     console.log('Error occured')
  //   }
  //   if(!geoData?.loading){
  //     console.log("latitude",geoData.latitude);
  //     console.log("longitude",geoData.longitude);
  //   }
  // }
  const flow = {
    start: {
      message: "Hello there! What is your name?",
      function: (params) => setName(params.userInput),
      path: "conversationType",
    },
    restaurant: {
      message: "This feature is under development. Pls. check later?",
      function: (params) => setName(params.userInput),
      path: "conversationType",
      chatDisabled: true,
      options: ["Start Again"],
    },
    trip: {
      message: "This feature is under development. Pls. check later?",
      function: (params) => setName(params.userInput),
      path: "conversationType",
      chatDisabled: true,
      options: ["Start Again"],
    },
    place: {
      message: "This feature is under development. Pls. check later?",
      function: (params) => setName(params.userInput),
      path: "conversationType",
      chatDisabled: true,
      options: ["Start Again"],
    },
    conversationType: {
      message: (params) => {
        return (
          (params.prevPath === "start" ? `Nice to meet you ${name}. ` : "") +
          `Choose what you want to do?`
        );
      },
      chatDisabled: true,
      options: ["Restaurant", "Trip", "Place", "Tour Guide"],
      path: (params) => {
        if (params.userInput === "Restaurant") {
          return "restaurant";
        } else if (params.userInput === "Trip") {
          return "trip";
        } else if (params.userInput === "Place") {
          return "place";
        } else if (params.userInput === "Tour Guide") {
          return "upload_image";
        }
      },
    },
    upload_image: {
      message: (params) =>
        `Please upload a photo of the place you want to share with the tour guide.`,
      chatDisabled: true,
      file: (params) => handleUpload(params),
      path: (params) => {
        return params.userInput === "Cancel"
          ? "conversationType"
          : "shareLocation";
      },
      // function: ()=>{
      //   getCurrentLocation();
      // },
      options: ["Cancel"],
    },
    reupload_image: {
      message: (params) => `Hi again ${name}, please upload the photo.`,
      chatDisabled: true,
      file: (params) => handleUpload(params),
      path: "shareLocation",
    },
    end: {
      transition: () => {
        return;
      },
      message: (params) => {
        return `Thank you. Lets talk again later. Bye for now.`;
      },
      options: ["Start Again"],
      path: "start",
      chatDisabled: true,
    },
    processing: {
      message: async (params) => {
        await params.injectMessage(
          "Your photo is being processed , Pls. wait ..."
        );
        // getCurrentLocation();
        const response = await tourguide(
          base64IMG,
          processedImg,
          geoData.latitude,
          geoData.longitude
        );
        setFetchingLocation(false);
        // console.log("tourguide response", response);
        setRecentResponse(response);
        // if (response.result === "success") {
        //   // await params.injectMessage(response.data);
        // } else if (response.result === "fail") {
        //   setRecentResponse(
        //     `An error occured while processing your request.${response.data} `
        //   );
        //   // await params.injectMessage(
        //   // `An error occured while processing your request.${response.data} `
        //   // );
        // }
        setisLoading(false);

        // console.log("Done");
        params.goToPath("showImage");
        // return 'Your request is processed, choose showImage option to view the image.'
      },
      // options: ["showImage"],
      chatDisabled: true,
      // function: async () => {
      //   const response = await tourguide(base64IMG, base64IMG, "Earth", 0, 0);
      //   setisLoading(false);
      //   // setTimeout(async () => {
      //   //   // setProcessedImg(
      //   //   //   mockImagesList[_.random(0, mockImagesList.length - 1, false)]
      //   //   // );
      //   //   // await params.goToPath('showImage');
      //   // }, 2000);
      // },
      path: (params) => {
        return "showImage";
      },
    },
    shareLocation: {
      message: async (params) => {
        setFetchingLocation(true);
        return `Pls. share your current location. If prompted for permissions, Pls. allow your current location to be shared. `;
      },
      chatDisabled: true,
      path: async (params) => {
        if (params.userInput === "Cancel") {
          return "conversationType";
        } else {
          setFetchingLocation(true);
          return "previewImage";
        }
      },
      options: ["Share location", "Cancel"],
    },
    previewImage: {
      message: async (params) => {
        // console.log("showImage", { params, isLoading });
        await params.injectMessage("Your location and photo are received ...");
        await params.injectMessage(
          "You can click anywhere in the image to get specific details or"
        );
        await params.injectMessage(
          "You can choose get general details option "
        );
        setProcessedImg(base64IMG);
      },
      component: (params) => {
        return (
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
            {/* TODO remove clicked positions image */}
            <img
              src={`${base64IMG}`}
              style={{ maxHeight: "100%", maxWidth: "100%" }}
              onClick={async (event) => {
                await params.injectMessage(
                  `Your request is accepted pls. wait, clicked positions [${
                    event?.nativeEvent?.offsetX || ""
                  },${event?.nativeEvent?.offsetY || ""}] `
                );
                const newBase64Img = await processSamImage(
                  base64IMG,
                  [...clicks, event].map((e) => [
                    e.nativeEvent?.offsetX,
                    e?.nativeEvent?.offsetY,
                  ])
                );
                if (newBase64Img.result === "success") {
                  setProcessedImg(newBase64Img.data);
                  setClicks((clickValues) => [...clickValues, event]);
                  setisLoading(false);
                  // console.log("Click listener", { event });
                  // console.log("clicked params", params);

                  // setProcessedImg(
                  //   newBase64Img
                  // );
                  setTimeout(async () => {
                    await params.goToPath("processing");
                  }, 1);
                } else {
                  await params.injectMessage(
                    `An error occured while processing your requests. ${newBase64Img.data}`
                  );
                }
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
        );
      },
      options: ["Show General Details", "Restart", "New Image", "End"],
      path: (params) => {
        if (params.userInput === "Restart") {
          return "conversationType";
        } else if (params.userInput === "New Image") {
          return "upload_image";
        } else if (params.userInput === "End") {
          return "end";
        } else if (params.userInput === " Show General Details") {
          return "processing";
        }
        // Add options to continue conversation
      },
      // thank: {
      //   message: async (params: any) => {
      //     await params.injectMessage("I am an injected message!");

      //     return "I am a return message!";
      //   },
      //   path: "start",
      // },
    },
    showImage: {
      message: async (params) => {
        // console.log("showImage", { params, isLoading });
        if (isLoading) {
          return "Your input is being processed , Pls. wait ...";
        } else {
          if (recentResponse.result === "success") {
            await params.injectMessage(new String(recentResponse.data).trim());
            return "You can click the desired area in the image, to know more details.";
          } else if (recentResponse.result === "fail") {
            await params.injectMessage(
              "Sorry. An error occured while processing your request."
            );
            return new String(recentResponse.data);
          }
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
            {/* TODO remove clicked positions image */}
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
                  // processedImg,
                  base64IMG,
                  [...clicks, event].map((e) => [
                    e.nativeEvent?.offsetX,
                    e?.nativeEvent?.offsetY,
                  ])
                );
                if (newBase64Img.result === "success") {
                  setProcessedImg(newBase64Img.data);
                  setClicks((clickValues) => [...clickValues, event]);
                  setisLoading(false);
                  // console.log("Click listener", { event });
                  // console.log("clicked params", params);

                  // setProcessedImg(
                  //   newBase64Img
                  // );
                  setTimeout(async () => {
                    await params.goToPath("processing");
                  }, 1);
                } else {
                  await params.injectMessage(
                    `An error occured while processing your requests. ${newBase64Img.data}`
                  );
                }
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
      options: ["Restart", "New Image", "End"],
      path: (params) => {
        if (params.userInput === "Restart") {
          return "conversationType";
        } else if (params.userInput === "New Image") {
          return "upload_image";
        } else if (params.userInput === "End") {
          return "end";
        }
        // Add options to continue conversation
      },
      // thank: {
      //   message: async (params: any) => {
      //     await params.injectMessage("I am an injected message!");

      //     return "I am a return message!";
      //   },
      //   path: "start",
      // },
    },
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
    chatHistory: { storageKey: "example_team_swag_chat" },
    botBubble: { simStream: true, streamSpeed: 15 },
    fileAttachment: {
      multiple: false,
      accept: ".jpg,.jpeg",
    },
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

  // console.log("Changes", { flow, clicks, messages });
  return (
    <div style={{ padding: "2rem" }}>
      <ChatBot
        settings={settings}
        // themes={themes}
        styles={styles}
        flow={flow}
      />
      {fetchingLocation && <GpsLocation setGeoData={setGeoData} />}
    </div>
  );
};
