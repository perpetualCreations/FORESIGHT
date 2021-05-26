# FORESIGHT
[![forthebadge](https://forthebadge.com/images/badges/contains-technical-debt.svg)](https://forthebadge.com) [![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com)

Flask web application for managing ARBITER, with expansion for usage as a front-end interface, in future BRIAH-layer applications.

Featuring basic password logins, powered by the Flask-Login project. 

## 3rd-Party Assets
For web sockets* support, FORESIGHT uses the SocketIO Javascript library,
loaded from [cdnjs.cloudflare.com](https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js).

The web interface stylesheet is loaded from [dreamerslegacy.xyz](https://dreamerslegacy.xyz/css/schema.min.css).

For users going off-grid, consider downloading 3rd-party assets from their sources,
and editing references in FORESIGHT's source code to the local copy.

## Notes
*[SocketIO is not a vanilla web socket library](https://socket.io/docs/v3/index.html#What-Socket-IO-is-not).
