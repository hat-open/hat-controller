
export type JsonArray = JsonData[];
export type JsonObject = {[key: string]: JsonData};
export type JsonData = (null | boolean | number | string | JsonArray |
                        JsonObject);

export interface Trigger {
    type: string;  // character '/' is reserved delimiter for type segments
    name: string;  // character '/' is reserved delimiter for name segments
    data: JsonData;
}

declare global {
    interface Units {}

    const units: Units;
}
