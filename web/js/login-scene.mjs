// Starts the sign-in bridge photo for the current part of the day in New York.
// Until a photo loads, the drawn bridge behind it shows, tinted for the hour.
import { loginBridge } from './bridge-assets.mjs';
import { startBridgeScene } from './bridge-scene.mjs';

const image = document.querySelector('img[data-bridge-scene="login"]');
if (image) window.bridgeScene = startBridgeScene(image, loginBridge);
