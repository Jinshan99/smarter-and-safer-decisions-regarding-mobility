import {
  Box,
  Button,
  ButtonGroup,
  Flex,
  HStack,
  IconButton,
  Input,
  SkeletonText,
  Text,
  Select,
} from '@chakra-ui/react'
import { FaLocationArrow, FaTimes } from 'react-icons/fa'

import {
  useJsApiLoader,
  GoogleMap,
  Marker,
  Autocomplete,
  DirectionsRenderer,
} from '@react-google-maps/api'
import { useRef, useState } from 'react'

const center = { lat: 34.0522, lng: -118.2437 }

function App() {
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: "AIzaSyBeVxc-RxQck9sQf2ZPE1t_rN4Krd94PpM",
    libraries: ['places'],
  })

  const [map, setMap] = useState(/** @type google.maps.Map */(null))
  const [directionsResponse, setDirectionsResponse] = useState(null)
  const [distance, setDistance] = useState('')
  const [duration, setDuration] = useState('')
  const modeRef = useRef(null);
  const crimeRef = useRef(null);

  /** @type React.MutableRefObject<HTMLInputElement> */
  const originRef = useRef()
  /** @type React.MutableRefObject<HTMLInputElement> */
  const destiantionRef = useRef()

  if (!isLoaded) {
    return <SkeletonText />
  }

  async function calculateRoute() {
    if (originRef.current.value === '' || destiantionRef.current.value === '') {
      return
    }
    // eslint-disable-next-line no-undef
    const directionsService = new google.maps.DirectionsService()
    const results = await directionsService.route({
      origin: originRef.current.value,
      destination: destiantionRef.current.value,
      // eslint-disable-next-line no-undef
      travelMode: google.maps.TravelMode[modeRef.current.value],
    })
    console.log(results)
    // results.routes[0].overview_path.forEach((point) => {
    //   console.log("latitude=" + point.lat() + ", longitude=" + point.lng())
    // })
    setDirectionsResponse(results)
    setDistance(results.routes[0].legs[0].distance.text)
    setDuration(results.routes[0].legs[0].duration.text)
  }

  function clearRoute() {
    setDirectionsResponse(null)
    setDistance('')
    setDuration('')
    originRef.current.value = ''
    destiantionRef.current.value = ''
  }

  function storeLatLng(overviewPath) {
    let array = [];
    overviewPath.forEach((point) => {
      array.push([point.lat(), point.lng()])
    })
    return array
  }


  async function saferoute() {
    const google = window.google
    if (originRef.current.value === '' || destiantionRef.current.value === '') {
      return
    }
    console.log(modeRef.current.value)

    // eslint-disable-next-line no-undef
    const directionsService = new window.google.maps.DirectionsService()
    const results = await directionsService.route({
      origin: originRef.current.value,
      destination: destiantionRef.current.value,
      // eslint-disable-next-line no-undef
      travelMode: google.maps.TravelMode[modeRef.current.value],
    })
    var allPoints = storeLatLng(results.routes[0].overview_path)
    var crime_target = crimeRef.current.value
    console.log(crime_target)
    // Make an HTTP request to Flask server
    const response = await fetch('http://127.0.0.1:5000/predict', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      route_points: allPoints,
      crime_type: crime_target
    })
  })
    // Process the reponse from the server
    const newStops = await response.json();
    const waypoints = newStops.predictions
    // Convert the 2D array of coordinates into an array of LatLng objects
    // Create an empty array to hold the LatLng objects
    const latLngWaypoints = [];
    // Loop through the waypoints and create a LatLng object for each one
    for (let i = 0; i < 20; i++) {
      latLngWaypoints.push({
        location: new google.maps.LatLng(waypoints[i][0],waypoints[i][1]),
        stopover: true
    }) 
    }
    console.log(latLngWaypoints)
    // Make a new route in google map
    const safeResults = await directionsService.route({
      origin: originRef.current.value,
      destination: destiantionRef.current.value,
      // eslint-disable-next-line no-undef
      waypoints: latLngWaypoints,
      travelMode: window.google.maps.TravelMode[modeRef.current.value],
    })

    // Add new stops to the route
    if (newStops.predictions) {
      const waypoints = newStops.predictions.map(point => ({
        location: new window.google.maps.LatLng(point[0], point[1]),
        stopover: true
      }));
      safeResults.routes[0].legs[0].via_waypoints = waypoints;
      console.log("check")
      console.log(safeResults)
    }
    setDirectionsResponse(safeResults)
    setDistance(safeResults.routes[0].legs[0].distance.text)
    setDuration(safeResults.routes[0].legs[0].duration.text)
  }

  return (
    <Flex
      position='relative'
      flexDirection='column'
      alignItems='center'
      h='100vh'
      w='100vw'
    >
      <Box position='absolute' left={0} top={0} h='100%' w='100%'>
        {/* Google Map Box */}
        <GoogleMap
          center={center}
          zoom={15}
          mapContainerStyle={{ width: '100%', height: '100%' }}
          options={{
            zoomControl: false,
            streetViewControl: false,
            mapTypeControl: false,
            fullscreenControl: false,
          }}
          onLoad={map => setMap(map)}
        >
          <Marker position={center} />
          {directionsResponse && (
            <DirectionsRenderer directions={directionsResponse} />
          )}
        </GoogleMap>
      </Box>
      <Box
        p={4}
        borderRadius='lg'
        m={4}
        bgColor='white'
        shadow='base'
        minW='container.md'
        zIndex='1'
      >
        <HStack spacing={2} justifyContent='space-between'>
          <Box flexGrow={1}>
            <Autocomplete>
              <Input type='text' placeholder='Origin' ref={originRef} />
            </Autocomplete>
          </Box>
          <Box flexGrow={1}>
            <Autocomplete>
              <Input
                type='text'
                placeholder='Destination'
                ref={destiantionRef}
              />
            </Autocomplete>
          </Box>

          <ButtonGroup>
            <Button colorScheme='pink' type='submit' onClick={calculateRoute}>
              Calculate Route
            </Button>
            {/* Model button */}
            <Button colorScheme='blue' type='submit' onClick={saferoute}>
              Safe Route
            </Button>

            <Box>
              <Select ref={modeRef}>
                <option value="WALKING">Walking</option>
                <option value="DRIVING">Driving</option>
                <option value="BICYCLING">Bicycling</option>
                <option value="TRANSIT">Transit</option>
              </Select>
            </Box>

            <IconButton
              aria-label='center back'
              icon={<FaTimes />}
              onClick={clearRoute}
            />
          </ButtonGroup>
        </HStack>

        <HStack spacing={4} mt={4} justifyContent='space-between'>
          <Text>Distance: {distance} </Text>
          <Text>Duration: {duration} </Text>
          <Box>
              <Select ref={crimeRef}>
                <option value="Assaults and threats"> Violent Crime </option>
                <option value="Robbery and related crimes"> Property Crime and Robbery </option>
                <option value="Others"> Domestic violence (Not recommend) </option>
              </Select>
            </Box>

          <IconButton
            aria-label='center back'
            icon={<FaLocationArrow />}
            isRound
            onClick={() => {
              map.panTo(center)
              map.setZoom(15)
            }}
          />
        </HStack>
        
      </Box>
    </Flex>
  )
}

export default App
