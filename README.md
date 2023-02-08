# Carbunco

Carbunco searches cheap gas stations in Spain.

You obtain a list of gas stations which are the cheaper at a certain distance,
so depending on how far you want to go, you will get cheaper prices.
Prices are obtained from the API provided by the Industry Ministry of Spain,
which are updated every half an hour.

Motivation: https://desconexionibex35.org/posts/2022/04/28/carburantes-quien-se-lo-lleva-crudo/ [ES]

You can use it as a desktop application or as command line interface providing the locations and the product as arguments.

![imatge](https://user-images.githubusercontent.com/532178/217429710-443a1ca0-4cb6-4be0-ad58-e7d68467229d.png)

## RoadMap

This application is still an alpha.
Some of the features I am willing to implement eventually are:

- Map: display the gas stations on a map.
- Auto-geolocation
- Installable binaries
- Mobile version
- Web version
- Real road distance (currently geodesic distance is used)
- Trail optimization: (instead of distance from a location, given a trip from A to B, considering the less diverting distance)
