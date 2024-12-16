import { useGeolocation } from "@uidotdev/usehooks";
import { useEffect } from "react";
export const GpsLocation = ({ setGeoData }: any) => {
  const geoData = useGeolocation();
  useEffect(() => {
    if (!geoData.loading) {
        setGeoData(geoData);
    }
  }, [geoData.loading]);

  return <></>;
};
