// src/mocks/handlers.js
import { http, HttpResponse } from "msw";
import { sourceTajMahalImage3 } from "./images";
import _ from "lodash";
const DEBUG_DELAY_MS = 4000;
const customDelayInMs = async (delayInMs = 2000) => {
  await new Promise((resolve) => {
    setTimeout(() => {
      resolve(true);
    }, delayInMs);
  });
};
const samprocessImage = (url: string) => {
  return http.post(url, async () => {
    await customDelayInMs(DEBUG_DELAY_MS);
    const sampleImage = sourceTajMahalImage3;
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
const tourguide = (url: string) => {
  return http.post(url, async () => {
    await customDelayInMs(10000);
    // const sampleImage = sourceTajMahalImage3;
    // // ...and respond to them using this JSON response.
    // const imageBuffer = await fetch(sampleImage).then((res) =>
    //   res.arrayBuffer()
    // );
    // return HttpResponse.json({
    //   id: 'c7b3d8e0-5e0b-4b0f-8b3a-3b9f4b3d3b3d',
    //   firstName: 'John',
    //   lastName: 'Maverick',
    // })
    const response = HttpResponse.text(
      `\nI'll help you find some interesting places to visit. Since you didn't specify a location, I'll first search for some exciting destinations.\nMaking a call to tool function SearchInternet with input {'query': 'Top tourist destinations for 2024 must-visit places'}.\nTool function executed successfully.\nLet me check out some details from the Travel + Leisure article about top destinations.\nMaking a call to tool function ReadWebsite with input {'url': 'https://www.travelandleisure.com/best-places-to-go-2024-8385979'}.\nTool function executed successfully.\nBased on the Travel + Leisure article about top destinations for 2024, I'll highlight some exciting places you might want to explore:\n\nTop Destinations for 2024:\n\n1. Coastal Campania, Italy\n- New luxury hotels opening\n- Beautiful coastal destinations like Amalfi, Capri, and Positano\n- New flight routes making it more accessible\n\n2. Los Cabos, Mexico\n- Stunning desert-meets-ocean landscape\n- New luxury resorts opening in 2024\n- 350 days of sunshine per year\n- Gorgeous beaches and golf courses\n\n3. Dominica\n- Known as the \"Nature Island\"\n- Tropical rainforests, hot springs, waterfalls\n- New resorts and eco-friendly developments\n- Sustainable tourism focus\n\n4. Mallorca, Spain\n- Sparkling waters and delicious food\n- New luxury hotels and resorts\n- Direct flights from the US\n- Beautiful coastline and historic properties\n\n5. Paris, France\n- Hosting the 2024 Summer Olympics\n- New luxury hotels\n- Exciting cultural events\n- Unique Olympic venues like beach volleyball near the Eiffel Tower\n\nWould you like me to provide more details about any of these destinations? Or are you interested in a specific type of travel experience?`,
      { status: 200 }
    );
    return response;
  });
};
export const handlers = [samprocessImage("/sam"), tourguide("/tourguide")];
