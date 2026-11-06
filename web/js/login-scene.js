/* Starts the time-of-day bridge photo on the sign-in page (New York time).
   Until a photo loads, the drawn bridge behind it shows, tinted for the hour. */
(function(){
  "use strict";
  if(!window.BridgeImages||!window.BridgeClock)return;
  new BridgeImages(BridgeClock,{
    login:{
      morning:  {src:"images/bridge/login-morning.jpg",  alt:"Empty lanes leading to the George Washington Bridge towers at sunrise"},
      afternoon:{src:"images/bridge/login-afternoon.jpg",alt:"Empty lanes leading to the George Washington Bridge towers in the afternoon"},
      night:    {src:"images/bridge/login-night.jpg",    alt:"Empty lanes leading to the lit George Washington Bridge towers at night"}
    }
  }).start();
})();
