// src/mocks/handlers.js
import { http, HttpResponse } from "msw";
import { sourceTajMahalImage2 } from "./images";
import _ from "lodash";
const DEBUG_DELAY_MS = 4000;
const samprocessImage = (url: string) => {
  return http.post(url, async () => {
    await _.delay(() => console.log("Do-nothing"), DEBUG_DELAY_MS);
    const sampleImage = sourceTajMahalImage2;
    // ...and respond to them using this JSON response.
    const imageBuffer = await fetch(sampleImage).then((res) =>
      res.arrayBuffer()
    );
    // return HttpResponse.json({
    //   id: 'c7b3d8e0-5e0b-4b0f-8b3a-3b9f4b3d3b3d',
    //   firstName: 'John',
    //   lastName: 'Maverick',
    // })
    const response = new HttpResponse(imageBuffer, {
      status: 200,
      headers: {
        "Content-Type": "image/jpeg",
      },
    });
    return response;
  });
};
export const handlers = [samprocessImage("/sam")];
