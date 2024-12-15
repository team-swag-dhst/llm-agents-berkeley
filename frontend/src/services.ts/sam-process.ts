import axios from "axios";
const baseUrl = process.env.BASE_URL;
const sam_url = `${baseUrl||''}/sam`;

const processSamImage = async (base64Image: string, clicks: Array<any>) => {
  try {
    const response = await axios.post(sam_url, { image: base64Image, clicks });
    let base64result: any = "";
    var reader = new window.FileReader();
    reader.readAsDataURL(response.data);
    reader.onload = () => {
      base64result = reader.result;
      console.log("API Response", response.data);
      return Promise.resolve({ result: "success", data: base64result });
    };
  } catch (e) {
    return Promise.resolve({ result: "failure", data: "e" });
  }
};
export { processSamImage };
