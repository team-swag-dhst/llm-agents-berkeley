import axios from "axios";
import { BASE_URL } from "../config";
const baseUrl = BASE_URL;
const tourguideurl = `${baseUrl}/tourguide`;
function _arrayBufferToBase64(buffer: any) {
  var binary = "";
  var bytes = new Uint8Array(buffer);
  var len = bytes.byteLength;
  for (var i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}
const tourguide = async (base64Image: string, maskedImage:string,lat:any=8.0777,lng:any=77.5539) => {
  try {
    const response = await axios.post(
      tourguideurl,
      { base_image: base64Image, masked_image:maskedImage,lat,lon:lng,stream:false },
    //   { responseType: "arraybuffer" }
    );
    // let base64result: any = "";
    // console.log("API Response", response.data);
    // base64result = Buffer.from(response.data, 'binary').toString('base64')
    // base64result = btoa(String.fromCharCode(...new Uint8Array(response.data)));
    // base64result =
    //   `data:image/jpeg;base64,` + _arrayBufferToBase64(response.data);

    // var reader = new window.FileReader();
    // reader.readAsDataURL(response.data);
    // reader.onload = () => {
    //   base64result = reader.result;
    // console.log("API Response", {data:response.data,base64result});
    return Promise.resolve({ result: "success", data: response.data });
    // };
  } catch (e) {
    console.log("Error", e);
    return Promise.resolve({ result: "fail", data: e });
  }
};
const tourguideStream = async (base64Image: string, maskedImage:string,location:string,lat:any,lng:any) => {
    try {
      const response = await axios.post(
        tourguideurl,
        { base_image: base64Image, masked_image:maskedImage,location,lat,lng,stream:true },
        { responseType: "arraybuffer" }
      );
      let base64result: any = "";
      // console.log("API Response", response.data);
      // base64result = Buffer.from(response.data, 'binary').toString('base64')
      // base64result = btoa(String.fromCharCode(...new Uint8Array(response.data)));
      base64result =
        `data:image/jpeg;base64,` + _arrayBufferToBase64(response.data);
  
      // var reader = new window.FileReader();
      // reader.readAsDataURL(response.data);
      // reader.onload = () => {
      //   base64result = reader.result;
      // console.log("API Response", {data:response.data,base64result});
      return Promise.resolve({ result: "success", data: base64result });
      // };
    } catch (e) {
      console.log("Error", e);
      return Promise.resolve({ result: "failure", data: e });
    }
  };
export { tourguide,tourguideStream };
