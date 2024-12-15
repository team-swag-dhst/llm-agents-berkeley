import axios from "axios";
const baseUrl = "";
const sam_url = `${baseUrl}/sam`;
function _arrayBufferToBase64(buffer: any) {
  var binary = "";
  var bytes = new Uint8Array(buffer);
  var len = bytes.byteLength;
  for (var i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}
const processSamImage = async (base64Image: string, clicks: Array<any>) => {
  try {
    const response = await axios.post(
      sam_url,
      { image: base64Image, clicks },
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
export { processSamImage };
