# FORESIGHT
[![forthebadge](https://forthebadge.com/images/badges/contains-technical-debt.svg)](https://forthebadge.com) [![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com)

Flexible Flask web application for defining front-end interfaces in a JSON file.

Made originally for managing ARBITER, with prospects for usage in future BRIAH-layer applications.

Featuring basic password logins, powered by the Flask-Login project. 

## 3rd-Party Assets
For web sockets support, FORESIGHT uses the SocketIO Javascript library,
loaded from [cdnjs.cloudflare.com](https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js). The authors of this project are not affiliated with the creators of SocketIO or its CDN distributor, you are encouraged to review [Cloudflare's Privacy Policy](https://www.cloudflare.com/privacypolicy/). 

The web interface stylesheet is loaded from [dreamerslegacy.xyz](https://dreamerslegacy.xyz/css/schema.min.css). Please note, the web service handling stylesheet requests is owned by the author of this project. Your IP and agent string may be logged for security purposes, and effective starting May 30th of 2021, will be deleted monthly to protect your privacy. This information will not be shared with other parties.

For users going off-grid, consider downloading 3rd-party assets from their sources,
and editing references in FORESIGHT's source code to the local copy.
