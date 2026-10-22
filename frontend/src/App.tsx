import { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import agricultureVideo from "./assets/agriculturevid.mp4";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

type Language = "en" | "te" | "hi";

type LocationData = {
  latitude: number;
  longitude: number;
  name?: string;
  districtId?: string;
  districtName?: string;
  accuracy?: string;
};

type District = {
  district_id: number;
  district_name: string;
  lgd_id: string | null;
  name: string;
};

type Town = {
  id: string;
  town_id: string;
  name: string;
  town_name: string;
  subdistrict_code: string;
  village_count: number;
};

type Village = {
  village_code: string;
  village_name: string;
  subdistrict_code: string;
  subdistrict_name: string;
  pincode: string | null;
};

type Market = {
  market: string;
  market_id?: number | null;
  date: string | null;
  variety: string | null;
  arrivals: number | null;
  min_price: number | null;
  modal_price: number | null;
  max_price: number | null;
  distance_km: number | null;
  market_latitude?: number | null;
  market_longitude?: number | null;
  current_price_available: boolean;
  price_status: string;
  price_source?: string;
  price_is_estimated?: boolean;
  transport_cost?: number | null;
  transport_cost_per_quintal?: number | null;
  net_price_per_quintal?: number | null;
  net_return?: number | null;
  overall_score?: number | null;
  distance_category?: string;
  market_quality?: string;
  is_best_option?: boolean;
};

type PriceResponse = {
  state: string;
  crop: string;
  year?: string;
  count: number;
  average_modal_price: number | null;
  telangana_average_price?: number | null;

  highest_market: {
    market: string;
    price: number;
    date: string;
    variety: string;
  } | null;

  nearest_market: Market | null;
  best_nearby_market: Market | null;

  recommendation_type?: string | null;
  recommendation_label?: string | null;
  recommendation_explanation: string | null;
  recommendation_status?: string | null;

  recommendation_settings?: {
    quantity_quintals: number;
    transport_cost_per_km_per_quintal: number;
    soft_distance_limit_km: number;
    hard_distance_limit_km: number;
  };

  markets: Market[];
  alternatives: Market[];
  nearby_alternatives: Market[];

  market_master_count: number;
  actual_price_market_count?: number;
  estimated_price_market_count?: number;
  markets_with_coordinates?: number;
};

type GeneralPrice = {
  crop: string;
  average_price: number | null;
  highest_price: number | null;
  highest_market: string | null;
  highest_date: string | null;
  record_count: number;
  status: string;
};

const CROPS = [
  { key: "maize", label: "🌽 Maize" },
  { key: "rice", label: "🌾 Rice" },
  { key: "cotton", label: "☁️ Cotton" },
  { key: "groundnut", label: "🥜 Groundnut" },
  { key: "banana", label: "🍌 Banana" },
];

const TEXT = {
  en: {
    language: "Language",
    english: "English",
    telugu: "తెలుగు",
    hindi: "हिन्दी",

    sellSmarter: "Sell Smarter.",
    betterPrice: "Get a Better Price.",
    subtitle: "Find the right place to sell your crop.",

    findMarket: "Find Best Place to Sell",
    todaysPrices: "Today's Crop Prices",

    generalPricing: "General Pricing",
    generalSubtitle: "Telangana statewide crop prices",

    chooseLocation: "Choose Your Location",
    useMyLocation: "Use My Location",
    chooseAnother: "Choose Another Location",

    locationUnavailable: "Location unavailable",
    detecting: "Detecting location...",

    locationDescription:
      "Use your current location or select your district, mandal and village.",

    exampleLocation: "e.g. Achampet, Nagarkurnool",

    findLocation: "Use This Location",
    findingLocation: "Finding location...",

    chooseDistrict: "Choose district",
    chooseTown: "Choose mandal / town",
    chooseVillage: "Choose village",

    back: "Back",
    close: "Close",

    chooseCrop: "Choose Crop",
    quantity: "Quantity",
    quintals: "quintals",
    quantityHelp:
      "Used for transport and net-return estimates.",

    compare: "Compare Markets",
    loading: "Loading...",
    retry: "Try Again",

    currentMarketPrices: "Current Market Prices",

    average: "Average",
    highest: "Highest Price",
    nearest: "Nearest Market",
    best: "Best Economic Option",

    effective: "Effective Price",
    transport: "Transport",
    netReturn: "Net Return",
    distance: "Distance",

    market: "Market",
    date: "Date",
    variety: "Variety",
    modal: "Modal",
    status: "Status",

    alternatives: "Alternatives",
    nearbyAlternatives: "Nearby Alternatives",

    noBest: "No market with a calculable price was found.",
    noData: "No current price data available for this crop.",
    noPrice: "No current price for this crop",

    footer:
      "Helping farmers compare markets and make better selling decisions.",

    perQuintal: "per quintal",
    currentPrice: "Current price",

    noNearby:
      "No nearby market with a calculable price was found.",

    showAll: "Show All",
    showLess: "Show Less",

    estimated:
      "Estimated from Telangana statewide average",

    currentAgmarknet:
      "Current AGMARKNET price",
  },

  te: {
    language: "భాష",
    english: "English",
    telugu: "తెలుగు",
    hindi: "హిందీ",

    sellSmarter: "తెలివిగా అమ్మండి.",
    betterPrice: "మెరుగైన ధర పొందండి.",
    subtitle:
      "మీ పంటను అమ్మడానికి సరైన మార్కెట్‌ను కనుగొనండి.",

    findMarket: "ఉత్తమ మార్కెట్‌ను కనుగొనండి",
    todaysPrices: "ఈరోజు పంట ధరలు",

    generalPricing: "సాధారణ ధరలు",
    generalSubtitle:
      "తెలంగాణ రాష్ట్రవ్యాప్తంగా పంట ధరలు",

    chooseLocation: "మీ ప్రదేశాన్ని ఎంచుకోండి",
    useMyLocation: "నా ప్రదేశాన్ని ఉపయోగించండి",
    chooseAnother: "మరో ప్రదేశాన్ని ఎంచుకోండి",

    locationUnavailable: "ప్రదేశం అందుబాటులో లేదు",
    detecting: "ప్రదేశాన్ని గుర్తిస్తోంది...",

    locationDescription:
      "మీ ప్రస్తుత ప్రదేశాన్ని ఉపయోగించండి లేదా జిల్లా, మండలం, గ్రామాన్ని ఎంచుకోండి.",

    exampleLocation: "ఉదా: Achampet, Nagarkurnool",

    findLocation: "ఈ ప్రదేశాన్ని ఉపయోగించండి",
    findingLocation: "ప్రదేశాన్ని కనుగొంటోంది...",

    chooseDistrict: "జిల్లాను ఎంచుకోండి",
    chooseTown: "మండలం / పట్టణం ఎంచుకోండి",
    chooseVillage: "గ్రామాన్ని ఎంచుకోండి",

    back: "వెనుకకు",
    close: "మూసివేయి",

    chooseCrop: "పంటను ఎంచుకోండి",
    quantity: "పరిమాణం",
    quintals: "క్వింటాళ్లు",
    quantityHelp:
      "రవాణా మరియు నికర రాబడిని అంచనా వేయడానికి.",

    compare: "మార్కెట్లను పోల్చండి",
    loading: "లోడ్ అవుతోంది...",
    retry: "మళ్లీ ప్రయత్నించండి",

    currentMarketPrices: "ప్రస్తుత మార్కెట్ ధరలు",

    average: "సగటు",
    highest: "అత్యధిక ధర",
    nearest: "సమీప మార్కెట్",
    best: "ఉత్తమ ఆర్థిక ఎంపిక",

    effective: "ప్రభావవంతమైన ధర",
    transport: "రవాణా",
    netReturn: "నికర రాబడి",
    distance: "దూరం",

    market: "మార్కెట్",
    date: "తేదీ",
    variety: "రకం",
    modal: "మోడల్",
    status: "స్థితి",

    alternatives: "ప్రత్యామ్నాయాలు",
    nearbyAlternatives: "సమీప ప్రత్యామ్నాయాలు",

    noBest:
      "లెక్కించగల ధర ఉన్న మార్కెట్ కనుగొనబడలేదు.",
    noData:
      "ఈ పంటకు ప్రస్తుత ధర సమాచారం లేదు.",
    noPrice:
      "ఈ పంటకు ప్రస్తుత ధర లేదు",

    footer:
      "రైతులు మార్కెట్లను పోల్చి మంచి అమ్మకపు నిర్ణయాలు తీసుకోవడంలో సహాయం చేస్తుంది.",

    perQuintal: "క్వింటాల్‌కు",
    currentPrice: "ప్రస్తుత ధర",

    noNearby:
      "సమీపంలో లెక్కించగల ధర ఉన్న మార్కెట్ లేదు.",

    showAll: "అన్నీ చూపించు",
    showLess: "తక్కువ చూపించు",

    estimated:
      "తెలంగాణ రాష్ట్ర సగటు ఆధారంగా అంచనా",

    currentAgmarknet:
      "ప్రస్తుత AGMARKNET ధర",
  },

  hi: {
    language: "भाषा",
    english: "English",
    telugu: "తెలుగు",
    hindi: "हिन्दी",

    sellSmarter: "समझदारी से बेचें।",
    betterPrice: "बेहतर कीमत पाएं।",
    subtitle:
      "अपनी फसल बेचने के लिए सही बाजार खोजें।",

    findMarket: "सबसे अच्छा बाजार खोजें",
    todaysPrices: "आज की फसल कीमतें",

    generalPricing: "सामान्य कीमतें",
    generalSubtitle:
      "तेलंगाना की राज्यव्यापी फसल कीमतें",

    chooseLocation: "अपना स्थान चुनें",
    useMyLocation: "मेरा स्थान इस्तेमाल करें",
    chooseAnother: "दूसरा स्थान चुनें",

    locationUnavailable: "स्थान उपलब्ध नहीं",
    detecting: "स्थान खोजा जा रहा है...",

    locationDescription:
      "अपना वर्तमान स्थान इस्तेमाल करें या जिला, मंडल और गांव चुनें।",

    exampleLocation: "उदा: Achampet, Nagarkurnool",

    findLocation: "यह स्थान इस्तेमाल करें",
    findingLocation: "स्थान खोजा जा रहा है...",

    chooseDistrict: "जिला चुनें",
    chooseTown: "मंडल / शहर चुनें",
    chooseVillage: "गांव चुनें",

    back: "वापस",
    close: "बंद करें",

    chooseCrop: "फसल चुनें",
    quantity: "मात्रा",
    quintals: "क्विंटल",
    quantityHelp:
      "परिवहन और शुद्ध रिटर्न के अनुमान के लिए।",

    compare: "बाजारों की तुलना करें",
    loading: "लोड हो रहा है...",
    retry: "फिर कोशिश करें",

    currentMarketPrices: "वर्तमान बाजार कीमतें",

    average: "औसत",
    highest: "सबसे अधिक कीमत",
    nearest: "सबसे नजदीकी बाजार",
    best: "सबसे अच्छा आर्थिक विकल्प",

    effective: "प्रभावी कीमत",
    transport: "परिवहन",
    netReturn: "शुद्ध रिटर्न",
    distance: "दूरी",

    market: "बाजार",
    date: "तारीख",
    variety: "किस्म",
    modal: "मॉडल",
    status: "स्थिति",

    alternatives: "विकल्प",
    nearbyAlternatives: "पास के विकल्प",

    noBest:
      "लाभ की गणना के लिए कोई बाजार नहीं मिला।",

    noData:
      "इस फसल के लिए वर्तमान कीमत उपलब्ध नहीं है.",

    noPrice:
      "इस फसल के लिए वर्तमान कीमत नहीं",

    footer:
      "किसानों को बाजारों की तुलना करने और बेहतर बिक्री निर्णय लेने में मदद करता है।",

    perQuintal: "प्रति क्विंटल",
    currentPrice: "वर्तमान कीमत",

    noNearby:
      "पास में गणना योग्य कीमत वाला बाजार नहीं मिला।",

    showAll: "सभी दिखाएं",
    showLess: "कम दिखाएं",

    estimated:
      "तेलंगाना राज्य औसत के आधार पर अनुमान",

    currentAgmarknet:
      "वर्तमान AGMARKNET कीमत",
  },
} as const;

type Text = typeof TEXT.en;


function money(
  value: number | null | undefined,
) {
  if (
    value == null ||
    !Number.isFinite(Number(value))
  ) {
    return "—";
  }

  return `₹${Math.round(
    Number(value),
  ).toLocaleString("en-IN")}`;
}


function distance(
  value: number | null | undefined,
) {
  if (
    value == null ||
    !Number.isFinite(Number(value))
  ) {
    return "—";
  }

  return `${Number(value).toFixed(1)} km`;
}


function cropLabel(
  key: string,
) {
  return (
    CROPS.find(
      (crop) => crop.key === key,
    )?.label ??
    `🌱 ${key}`
  );
}


export default function App() {
  const [language, setLanguage] =
    useState<Language>("en");

  const t = TEXT[language] as Text;

  const [languageOpen, setLanguageOpen] =
    useState(false);

  const [locationModal, setLocationModal] =
    useState(false);

  const [manualMode, setManualMode] =
    useState(false);

  const [locationLoading, setLocationLoading] =
    useState(false);

  const [locationError, setLocationError] =
    useState("");

  const [location, setLocation] =
    useState<LocationData | null>(null);

  const [districts, setDistricts] =
    useState<District[]>([]);

  const [towns, setTowns] =
    useState<Town[]>([]);

  const [villages, setVillages] =
    useState<Village[]>([]);

  const [districtId, setDistrictId] =
    useState("");

  const [districtName, setDistrictName] =
    useState("");

  const [townCode, setTownCode] =
    useState("");

  const [townName, setTownName] =
    useState("");

  const [villageCode, setVillageCode] =
    useState("");

  const [villageName, setVillageName] =
    useState("");

  const [search, setSearch] =
    useState("");

  const [manualLoading, setManualLoading] =
    useState(false);

  const [townLoading, setTownLoading] =
    useState(false);

  const [villageLoading, setVillageLoading] =
    useState(false);

  const [crop, setCrop] =
    useState("maize");

  const [quantity, setQuantity] =
    useState("10");

  const [priceData, setPriceData] =
    useState<PriceResponse | null>(null);

  const [general, setGeneral] =
    useState<GeneralPrice[]>([]);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [
    showAllAlternatives,
    setShowAllAlternatives,
  ] = useState(false);

  // Prevent stale requests from overwriting newer selections.
  const townRequestId =
    useRef(0);

  const villageRequestId =
    useRef(0);


  // ======================================================
  // INITIAL LOAD
  // ======================================================

  useEffect(() => {
    let cancelled = false;

    async function loadInitialData() {
      try {
        const [
          districtResponse,
          generalResponse,
        ] = await Promise.all([
          fetch(
            `${API}/locations/districts?state=Telangana`,
          ),
          fetch(
            `${API}/prices/general`,
          ),
        ]);

        if (cancelled) return;

        if (districtResponse.ok) {
          const districtData =
            await districtResponse.json();

          setDistricts(
            Array.isArray(
              districtData?.districts,
            )
              ? districtData.districts
              : [],
          );
        } else {
          setDistricts([]);
        }

        if (generalResponse.ok) {
          const generalData =
            await generalResponse.json();

          setGeneral(
            Array.isArray(
              generalData?.prices,
            )
              ? generalData.prices
              : [],
          );
        } else {
          setGeneral([]);
        }
      } catch {
        if (!cancelled) {
          setDistricts([]);
          setGeneral([]);
        }
      }
    }

    loadInitialData();

    return () => {
      cancelled = true;
    };
  }, []);


  // ======================================================
  // LOAD MANDALS
  // ======================================================

  async function loadTowns(
    nextDistrictId: string,
    name: string,
  ) {
    const requestId =
      ++townRequestId.current;

    setTownCode("");
    setTownName("");
    setVillageCode("");
    setVillageName("");

    setVillages([]);
    setTowns([]);

    if (!nextDistrictId) {
      return;
    }

    setTownLoading(true);
    setLocationError("");

    try {
      const url =
        `${API}/locations/towns` +
        `?district_id=${encodeURIComponent(
          nextDistrictId,
        )}` +
        `&district_name=${encodeURIComponent(
          name,
        )}`;

      const response =
        await fetch(url);

      const data =
        await response.json();

      if (
        requestId !==
        townRequestId.current
      ) {
        return;
      }

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Could not load mandals.",
        );
      }

      const receivedTowns =
        Array.isArray(data?.towns)
          ? data.towns
          : [];

      setTowns(receivedTowns);

      if (receivedTowns.length === 0) {
        setLocationError(
          `No mandals were returned for ${name}.`,
        );
      }
    } catch (error: any) {
      if (
        requestId ===
        townRequestId.current
      ) {
        setTowns([]);

        setLocationError(
          error?.message ||
            "Could not load mandals.",
        );
      }
    } finally {
      if (
        requestId ===
        townRequestId.current
      ) {
        setTownLoading(false);
      }
    }
  }


  // ======================================================
  // LOAD VILLAGES
  // ======================================================

  async function loadVillages(
    nextTownCode: string,
  ) {
    const requestId =
      ++villageRequestId.current;

    setVillageCode("");
    setVillageName("");
    setVillages([]);

    if (!nextTownCode) {
      return;
    }

    setVillageLoading(true);
    setLocationError("");

    try {
      const response =
        await fetch(
          `${API}/locations/villages?subdistrict_code=${encodeURIComponent(
            nextTownCode,
          )}`,
        );

      const data =
        await response.json();

      if (
        requestId !==
        villageRequestId.current
      ) {
        return;
      }

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Could not load villages.",
        );
      }

      const receivedVillages =
        Array.isArray(
          data?.villages,
        )
          ? data.villages
          : [];

      setVillages(
        receivedVillages,
      );

      if (
        receivedVillages.length === 0
      ) {
        setLocationError(
          "No villages were returned for this mandal.",
        );
      }
    } catch (error: any) {
      if (
        requestId ===
        villageRequestId.current
      ) {
        setVillages([]);

        setLocationError(
          error?.message ||
            "Could not load villages.",
        );
      }
    } finally {
      if (
        requestId ===
        villageRequestId.current
      ) {
        setVillageLoading(false);
      }
    }
  }


  // ======================================================
  // APPLY COORDINATES
  // ======================================================

  function applyCoordinates(
    data: any,
    fallbackName: string,
  ) {
    const latitude = Number(
      data?.latitude,
    );

    const longitude = Number(
      data?.longitude,
    );

    if (
      !Number.isFinite(latitude) ||
      !Number.isFinite(longitude)
    ) {
      throw new Error(
        "The location service did not return valid coordinates.",
      );
    }

    const selectedDistrictName =
      data?.district_name ||
      districtName ||
      "";

    const selectedDistrictId =
      data?.district_id != null
        ? String(data.district_id)
        : districtId || "";

    const accuracy =
      data?.accuracy ||
      undefined;

    let displayName =
      data?.display_name ||
      fallbackName ||
      "Selected location";

    if (
      accuracy &&
      accuracy !== "village"
    ) {
      displayName =
        `${fallbackName} · ${accuracy.replace(
          "_",
          " ",
        )}`;
    }

    setLocation({
      latitude,
      longitude,
      name: displayName,
      districtId:
        selectedDistrictId ||
        undefined,
      districtName:
        selectedDistrictName ||
        undefined,
      accuracy,
    });

    if (
      selectedDistrictId
    ) {
      setDistrictId(
        selectedDistrictId,
      );
    }

    if (
      selectedDistrictName
    ) {
      setDistrictName(
        selectedDistrictName,
      );
    }
  }


  // ======================================================
  // SELECTED HIERARCHY -> COORDINATES
  // ======================================================

  async function geocodeSelection() {
    setManualLoading(true);
    setLocationError("");

    try {
      // --------------------------------------------------
      // VILLAGE SELECTED
      //
      // IMPORTANT FIX:
      // Use village_code, not free-text geocoding.
      // --------------------------------------------------

      if (villageCode) {
        const response =
          await fetch(
            `${API}/locations/hierarchy/geocode?village_code=${encodeURIComponent(
              villageCode,
            )}`,
          );

        const data =
          await response.json();

        if (!response.ok) {
          throw new Error(
            data?.detail ||
              "Could not determine coordinates for the selected village.",
          );
        }

        applyCoordinates(
          data,
          `${villageName}, ${townName}, ${districtName}`,
        );

        setLocationModal(false);
        setManualMode(false);

        return;
      }

      // --------------------------------------------------
      // MANDAL SELECTED
      // --------------------------------------------------

      if (townName) {
        await chooseManual(
          `${townName}, ${districtName}, Telangana, India`,
        );

        return;
      }

      // --------------------------------------------------
      // DISTRICT SELECTED
      // --------------------------------------------------

      if (districtName) {
        await chooseManual(
          `${districtName}, Telangana, India`,
        );

        return;
      }

      throw new Error(
        "Please select a district, mandal, or village.",
      );
    } catch (error: any) {
      setLocationError(
        error?.message ||
          "Could not determine this location.",
      );
    } finally {
      setManualLoading(false);
    }
  }


  // ======================================================
  // FREE TEXT LOCATION
  // ======================================================

  async function chooseManual(
    query: string,
  ) {
    setManualLoading(true);
    setLocationError("");

    try {
      const response =
        await fetch(
          `${API}/locations/geocode?query=${encodeURIComponent(
            query,
          )}`,
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Could not find this location.",
        );
      }

      applyCoordinates(
        data,
        query,
      );

      setLocationModal(false);
      setManualMode(false);
    } catch (error: any) {
      setLocationError(
        error?.message ||
          "Could not find this location.",
      );
    } finally {
      setManualLoading(false);
    }
  }


  // ======================================================
  // CURRENT GPS LOCATION
  // ======================================================

  function detectLocation() {
    setLocationLoading(true);
    setLocationError("");

    if (!navigator.geolocation) {
      setLocationError(
        "Geolocation is not supported by this browser.",
      );

      setLocationLoading(false);

      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const latitude =
          position.coords.latitude;

        const longitude =
          position.coords.longitude;

        const fallbackName =
          `${latitude.toFixed(
            5,
          )}, ${longitude.toFixed(5)}`;

        try {
          const response =
            await fetch(
              `${API}/locations/geocode?query=${encodeURIComponent(
                `${latitude},${longitude}`,
              )}`,
            );

          if (response.ok) {
            const data =
              await response.json();

            applyCoordinates(
              data,
              fallbackName,
            );
          } else {
            setLocation({
              latitude,
              longitude,
              name: fallbackName,
            });
          }
        } catch {
          setLocation({
            latitude,
            longitude,
            name: fallbackName,
          });
        }

        setLocationLoading(false);
        setLocationModal(false);
        setManualMode(false);
      },

      (error) => {
        setLocationLoading(false);

        if (
          error.code ===
          error.PERMISSION_DENIED
        ) {
          setLocationError(
            "Location permission was denied. Allow location access for localhost in Chrome.",
          );
        } else if (
          error.code ===
          error.TIMEOUT
        ) {
          setLocationError(
            "Location detection timed out. Try again or choose your village manually.",
          );
        } else {
          setLocationError(
            "Could not determine your current location.",
          );
        }
      },

      {
        enableHighAccuracy: true,
        timeout: 20000,
        maximumAge: 60000,
      },
    );
  }


  // ======================================================
  // COMPARE MARKETS
  // ======================================================

  async function compare() {
    setLoading(true);
    setError("");

    try {
      const quantityValue = Math.max(
        0.1,
        Number(quantity) || 10,
      );

      const params =
        new URLSearchParams({
          crop,
          quantity_quintals:
            String(quantityValue),
        });

      if (location) {
        params.set(
          "latitude",
          String(
            location.latitude,
          ),
        );

        params.set(
          "longitude",
          String(
            location.longitude,
          ),
        );
      } else {
        throw new Error(
          "Please choose a location before comparing markets.",
        );
      }

      if (districtId) {
        params.set(
          "district_id",
          districtId,
        );
      }

      const response =
        await fetch(
          `${API}/prices?${params.toString()}`,
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Failed to load prices.",
        );
      }

      setPriceData(data);
      setShowAllAlternatives(false);

      document
        .getElementById(
          "market-results",
        )
        ?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
    } catch (error: any) {
      setError(
        error?.message ||
          "Failed to load market prices.",
      );

      setPriceData(null);
    } finally {
      setLoading(false);
    }
  }


  // ======================================================
  // GENERAL PRICE REFRESH
  // ======================================================

  async function refreshGeneral() {
    try {
      const response =
        await fetch(
          `${API}/prices/general`,
        );

      if (!response.ok) {
        return;
      }

      const data =
        await response.json();

      setGeneral(
        Array.isArray(
          data?.prices,
        )
          ? data.prices
          : [],
      );
    } catch {
      // Keep existing data.
    }
  }


  // ======================================================
  // DERIVED DATA
  // ======================================================

  const alternatives =
    useMemo(
      () =>
        priceData?.alternatives ||
        [],
      [priceData],
    );

  const shownAlternatives =
    showAllAlternatives
      ? alternatives
      : alternatives.slice(
          0,
          10,
        );

  const locationText =
    location?.name ||
    "Choose your location";


  // ======================================================
  // RENDER
  // ======================================================

  return (
    <div className="app">

      {/* =================================================
          HERO
      ================================================= */}

      <section className="hero">

        <video
          className="background-video"
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
        >
          <source
            src={agricultureVideo}
            type="video/mp4"
          />
        </video>

        <div className="video-overlay" />

        <header className="navbar">

          <div className="brand">
            🌾 <span>CropConn8t</span>
          </div>

          <div className="language-wrapper">

            <button
              className="language-button"
              onClick={() =>
                setLanguageOpen(
                  !languageOpen,
                )
              }
            >
              🌐 {t.language}
            </button>

            {languageOpen && (
              <div className="language-menu">

                <button
                  onClick={() => {
                    setLanguage("en");
                    setLanguageOpen(false);
                  }}
                >
                  🇬🇧 {t.english}
                </button>

                <button
                  onClick={() => {
                    setLanguage("te");
                    setLanguageOpen(false);
                  }}
                >
                  🇮🇳 {t.telugu}
                </button>

                <button
                  onClick={() => {
                    setLanguage("hi");
                    setLanguageOpen(false);
                  }}
                >
                  🇮🇳 {t.hindi}
                </button>

              </div>
            )}

          </div>

        </header>


        <div className="hero-content">

          <h1>
            {t.sellSmarter}
            <br />
            {t.betterPrice}
          </h1>

          <p>
            {t.subtitle}
          </p>

          <div className="hero-actions">

            <button
              className="primary-button"
              onClick={() =>
                setLocationModal(true)
              }
            >
              🔎 {t.findMarket}
            </button>

            <button
              className="secondary-button"
              onClick={() =>
                document
                  .getElementById(
                    "general-pricing",
                  )
                  ?.scrollIntoView({
                    behavior: "smooth",
                  })
              }
            >
              📊 {t.todaysPrices}
            </button>

          </div>

          <button
            className="location-pill"
            onClick={() => {
              setLocationError("");
              setLocationModal(true);
            }}
          >
            📍 {locationText}
          </button>

        </div>

      </section>


      {/* =================================================
          GENERAL PRICING
      ================================================= */}

      <section
        id="general-pricing"
        className="section general-section"
      >

        <div className="section-header">

          <div>

            <span className="eyebrow">
              TELANGANA
            </span>

            <h2>
              {t.generalPricing}
            </h2>

            <p className="section-subtitle">
              {t.generalSubtitle}
            </p>

          </div>

          <button
            className="refresh-button"
            onClick={refreshGeneral}
          >
            ↻
          </button>

        </div>


        <div className="general-grid">

          {general.map(
            (item, index) => (
              <div
                className="general-card"
                key={`${item.crop}-${index}`}
              >

                <div className="crop-name">
                  {cropLabel(
                    item.crop,
                  )}
                </div>

                <div className="general-main">

                  <div>
                    <span>
                      {t.average}
                    </span>

                    <strong>
                      {money(
                        item.average_price,
                      )}
                    </strong>

                    <small>
                      {t.perQuintal}
                    </small>
                  </div>

                  <div>
                    <span>
                      {t.highest}
                    </span>

                    <strong>
                      {money(
                        item.highest_price,
                      )}
                    </strong>

                    <small>
                      {t.perQuintal}
                    </small>
                  </div>

                </div>

                <div className="general-footer">

                  <div>
                    📍{" "}
                    {item.highest_market ||
                      "—"}
                  </div>

                  <div>
                    📅{" "}
                    {item.highest_date ||
                      "—"}
                  </div>

                </div>

              </div>
            ),
          )}

        </div>

      </section>


      {/* =================================================
          MARKET COMPARISON
      ================================================= */}

      <section
        id="market-results"
        className="section comparison-section"
      >

        <div className="section-header">

          <div>

            <span className="eyebrow">
              CROP MARKET
            </span>

            <h2>
              {t.currentMarketPrices}
            </h2>

            <p className="section-subtitle">
              Compare current prices,
              alternatives, distance and
              estimated net return.
            </p>

          </div>

        </div>


        {/* LOCATION SUMMARY */}

        <div className="location-control">

          <div>

            <strong>
              {t.chooseLocation}
            </strong>

            <p>
              {locationText}
            </p>

          </div>

          <button
            className="outline-button"
            onClick={() =>
              setLocationModal(true)
            }
          >
            📍 {t.chooseLocation}
          </button>

        </div>


        {/* CROP */}

        <div className="crop-selector">

          <label>
            {t.chooseCrop}
          </label>

          <div className="crop-buttons">

            {CROPS.map(
              (item) => (
                <button
                  key={item.key}
                  className={`crop-button ${
                    crop === item.key
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    setCrop(
                      item.key,
                    )
                  }
                >
                  {item.label}
                </button>
              ),
            )}

          </div>

        </div>


        {/* QUANTITY */}

        <div className="quantity-row">

          <div>

            <label>
              {t.quantity}
            </label>

            <input
              type="number"
              min="0.1"
              step="0.1"
              value={quantity}
              onChange={(event) =>
                setQuantity(
                  event.target.value,
                )
              }
            />

            <span>
              {t.quintals}
            </span>

          </div>

          <small>
            {t.quantityHelp}
          </small>

        </div>


        {/* LOCATION SELECTORS */}

        <div className="location-select-grid">

          {/* DISTRICT */}

          <div className="field">

            <label>
              {t.chooseDistrict}
            </label>

            <select
              value={districtId}
              onChange={async (event) => {

                const selected =
                  districts.find(
                    (item) =>
                      String(
                        item.district_id,
                      ) ===
                      event.target.value,
                  );

                const nextId =
                  event.target.value;

                const nextName =
                  selected?.district_name ||
                  "";

                setDistrictId(
                  nextId,
                );

                setDistrictName(
                  nextName,
                );

                setLocation(
                  null,
                );

                setPriceData(
                  null,
                );

                await loadTowns(
                  nextId,
                  nextName,
                );
              }}
            >

              <option value="">
                {t.chooseDistrict}
              </option>

              {districts.map(
                (item) => (
                  <option
                    key={
                      item.district_id
                    }
                    value={
                      item.district_id
                    }
                  >
                    {
                      item.district_name
                    }
                  </option>
                ),
              )}

            </select>

          </div>


          {/* MANDAL */}

          <div className="field">

            <label>
              {t.chooseTown}
            </label>

            <select
              disabled={
                !districtId ||
                townLoading
              }
              value={townCode}
              onChange={async (event) => {

                const selected =
                  towns.find(
                    (item) =>
                      item.id ===
                      event.target.value,
                  );

                const nextCode =
                  event.target.value;

                setTownCode(
                  nextCode,
                );

                setTownName(
                  selected?.town_name ||
                    "",
                );

                setLocation(
                  null,
                );

                setPriceData(
                  null,
                );

                await loadVillages(
                  nextCode,
                );
              }}
            >

              <option value="">
                {townLoading
                  ? "Loading mandals..."
                  : t.chooseTown}
              </option>

              {towns.map(
                (item) => (
                  <option
                    key={item.id}
                    value={item.id}
                  >
                    {item.town_name} (
                    {
                      item.village_count
                    }
                    )
                  </option>
                ),
              )}

            </select>

          </div>


          {/* VILLAGE */}

          <div className="field">

            <label>
              {t.chooseVillage}
            </label>

            <select
              disabled={
                !townCode ||
                villageLoading
              }
              value={villageCode}
              onChange={(event) => {

                const selected =
                  villages.find(
                    (item) =>
                      item.village_code ===
                      event.target.value,
                  );

                setVillageCode(
                  event.target.value,
                );

                setVillageName(
                  selected?.village_name ||
                    "",
                );

                setLocation(
                  null,
                );

                setPriceData(
                  null,
                );
              }}
            >

              <option value="">
                {villageLoading
                  ? "Loading villages..."
                  : t.chooseVillage}
              </option>

              {villages.map(
                (item) => (
                  <option
                    key={
                      item.village_code
                    }
                    value={
                      item.village_code
                    }
                  >
                    {
                      item.village_name
                    }

                    {item.pincode
                      ? ` — ${item.pincode}`
                      : ""}
                  </option>
                ),
              )}

            </select>

          </div>


          {/* USE SELECTED LOCATION */}

          <button
            className="use-selection"
            onClick={
              geocodeSelection
            }
            disabled={
              manualLoading ||
              (
                !districtName &&
                !townName &&
                !villageName
              )
            }
          >
            {manualLoading
              ? t.findingLocation
              : t.findLocation}
          </button>

        </div>


        {/* LOCATION ERROR */}

        {locationError && (
          <div className="location-error">
            {locationError}
          </div>
        )}


        {/* SEARCH */}

        <div className="manual-search-row">

          <input
            placeholder={
              t.exampleLocation
            }
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value,
              )
            }
            onKeyDown={(event) => {

              if (
                event.key === "Enter" &&
                search.trim()
              ) {
                chooseManual(
                  search.trim(),
                );
              }

            }}
          />

          <button
            className="outline-button"
            onClick={() => {

              if (
                search.trim()
              ) {
                chooseManual(
                  search.trim(),
                );
              }

            }}
          >
            {t.findLocation}
          </button>

        </div>


        {/* COMPARE */}

        <div className="compare-action">

          <button
            className="compare-button"
            onClick={compare}
            disabled={
              loading ||
              !location
            }
          >
            📊{" "}
            {loading
              ? t.loading
              : t.compare}
          </button>

        </div>


        {/* ERROR */}

        {error && (
          <div className="error-box">

            {error}

            <button
              onClick={compare}
            >
              {t.retry}
            </button>

          </div>
        )}


        {/* LOADING */}

        {loading && (
          <div className="loading-box">

            <div className="spinner" />

            {t.loading}

          </div>
        )}


        {/* =================================================
            RESULTS
        ================================================= */}

        {priceData &&
          !loading && (
            <div className="results-stack">

              {/* SUMMARY */}

              <div className="summary-grid">

                <div className="summary-card">

                  <span>
                    {t.average}
                  </span>

                  <strong>
                    {money(
                      priceData.average_modal_price,
                    )}
                  </strong>

                  <small>
                    {t.perQuintal}
                  </small>

                </div>


                <div className="summary-card">

                  <span>
                    🏆 {t.highest}
                  </span>

                  <strong>
                    {money(
                      priceData
                        .highest_market
                        ?.price,
                    )}
                  </strong>

                  <small>
                    {
                      priceData
                        .highest_market
                        ?.market
                    }
                  </small>

                  <small>
                    📅{" "}
                    {
                      priceData
                        .highest_market
                        ?.date
                    }
                  </small>

                </div>


                <div className="summary-card">

                  <span>
                    📍 {t.nearest}
                  </span>

                  <strong>
                    {money(
                      priceData
                        .nearest_market
                        ?.modal_price,
                    )}
                  </strong>

                  <small>
                    {
                      priceData
                        .nearest_market
                        ?.market ||
                      "—"
                    }
                  </small>

                  <small>
                    {distance(
                      priceData
                        .nearest_market
                        ?.distance_km,
                    )}
                  </small>

                </div>

              </div>


              {/* FALLBACK NOTICE */}

              {(
                priceData
                  .estimated_price_market_count ||
                0
              ) > 0 && (
                <div className="notice-box">
                  🟡{" "}
                  Some markets do not have
                  a current crop-specific
                  price. CropConn8t uses the
                  Telangana statewide
                  average as an estimate
                  for comparison.
                </div>
              )}


              {/* BEST MARKET */}

              {priceData.best_nearby_market ? (

                <div className="best-market">

                  <div className="best-badge">
                    🏆 {t.best}
                  </div>

                  <div className="best-content">

                    <div>

                      <h3>
                        {
                          priceData
                            .best_nearby_market
                            .market
                        }
                      </h3>

                      <p>
                        {
                          priceData
                            .best_nearby_market
                            .date ||
                          "Estimate"
                        }

                        {" • "}

                        {
                          priceData
                            .best_nearby_market
                            .variety ||
                          "—"
                        }
                      </p>

                      <p>
                        📍{" "}
                        {distance(
                          priceData
                            .best_nearby_market
                            .distance_km,
                        )}
                      </p>

                    </div>


                    <div>

                      <strong className="big-price">
                        {money(
                          priceData
                            .best_nearby_market
                            .modal_price,
                        )}
                      </strong>

                      <span>
                        {t.currentPrice}
                      </span>

                    </div>


                    <div>

                      <strong className="big-price">
                        {money(
                          priceData
                            .best_nearby_market
                            .net_price_per_quintal,
                        )}
                      </strong>

                      <span>
                        {t.effective}
                      </span>

                    </div>

                  </div>


                  <div className="best-metrics">

                    <div>

                      <span>
                        {t.transport}
                      </span>

                      <strong>
                        {money(
                          priceData
                            .best_nearby_market
                            .transport_cost,
                        )}
                      </strong>

                    </div>

                    <div>

                      <span>
                        {t.netReturn}
                      </span>

                      <strong>
                        {money(
                          priceData
                            .best_nearby_market
                            .net_return,
                        )}
                      </strong>

                    </div>

                    <div>

                      <span>
                        {t.status}
                      </span>

                      <strong>
                        {
                          priceData
                            .recommendation_status ||
                          priceData
                            .recommendation_label ||
                          "—"
                        }
                      </strong>

                    </div>

                  </div>


                  {priceData
                    .recommendation_explanation && (
                    <p className="recommendation-text">
                      💡{" "}
                      {
                        priceData
                          .recommendation_explanation
                      }
                    </p>
                  )}

                </div>

              ) : (

                <div className="no-best">

                  <strong>
                    {t.noBest}
                  </strong>

                  <br />

                  {priceData
                    .highest_market
                    ? `${t.highest}: ${priceData.highest_market.market} • ${money(
                        priceData.highest_market.price,
                      )}`
                    : ""}

                </div>
              )}


              {/* NEARBY */}

              <div className="alternative-block">

                <div className="table-heading">

                  <div>

                    <h3>
                      {
                        t.nearbyAlternatives
                      }
                    </h3>

                    <span>
                      {
                        priceData
                          .nearby_alternatives
                          .length
                      }{" "}
                      {t.alternatives}
                    </span>

                  </div>

                </div>


                {priceData
                  .nearby_alternatives
                  .length === 0 ? (

                  <div className="no-best">
                    {t.noNearby}
                  </div>

                ) : (

                  <div className="alternative-grid">

                    {priceData
                      .nearby_alternatives
                      .slice(0, 6)
                      .map(
                        (
                          market,
                          index,
                        ) => (

                          <div
                            className={`alternative-card ${
                              market.is_best_option
                                ? "best-alt"
                                : ""
                            }`}
                            key={`${market.market}-${index}`}
                          >

                            <div className="alt-title">

                              {market.is_best_option &&
                                "🏆 "}

                              {market.market}

                            </div>

                            <div className="alt-distance">
                              📍{" "}
                              {distance(
                                market.distance_km,
                              )}
                            </div>

                            <div className="alt-price">
                              {market.modal_price !=
                              null
                                ? money(
                                    market.modal_price,
                                  )
                                : "—"}
                            </div>

                            <div className="alt-status">

                              {market.price_is_estimated
                                ? `🟡 ${t.estimated}`
                                : market.current_price_available
                                ? `✅ ${t.currentAgmarknet}`
                                : `⚪ ${t.noPrice}`}

                            </div>

                          </div>

                        ),
                      )}

                  </div>

                )}

              </div>


              {/* ALL ALTERNATIVES */}

              <div className="table-heading">

                <div>

                  <h3>
                    {t.alternatives}
                  </h3>

                  <span>
                    {alternatives.length}{" "}
                    markets
                  </span>

                </div>


                {alternatives.length >
                  10 && (

                  <button
                    className="show-all-button"
                    onClick={() =>
                      setShowAllAlternatives(
                        (value) =>
                          !value,
                      )
                    }
                  >
                    {showAllAlternatives
                      ? t.showLess
                      : `${t.showAll} ${alternatives.length}`}
                  </button>

                )}

              </div>


              <div className="market-table">

                <div className="table-row table-head">

                  <span>
                    {t.market}
                  </span>

                  <span>
                    {t.date}
                  </span>

                  <span>
                    {t.modal}
                  </span>

                  <span>
                    {t.transport}
                  </span>

                  <span>
                    {t.effective}
                  </span>

                  <span>
                    {t.distance}
                  </span>

                  <span>
                    {t.status}
                  </span>

                </div>


                {shownAlternatives.map(
                  (
                    market,
                    index,
                  ) => (

                    <div
                      className={`table-row ${
                        market.is_best_option
                          ? "highlight-row"
                          : ""
                      }`}
                      key={`${market.market}-${market.date}-${index}`}
                    >

                      <span className="market-cell">

                        {market.is_best_option &&
                          "🏆 "}

                        {market.market}

                      </span>


                      <span>
                        {market.date ||
                          "Estimate"}
                      </span>


                      <span className="modal-cell">

                        {money(
                          market.modal_price,
                        )}

                      </span>


                      <span>
                        {money(
                          market.transport_cost,
                        )}
                      </span>


                      <span className="modal-cell">

                        {money(
                          market.net_price_per_quintal,
                        )}

                      </span>


                      <span>
                        {distance(
                          market.distance_km,
                        )}
                      </span>


                      <span>

                        {market.price_is_estimated
                          ? `🟡 ${t.estimated}`
                          : market.current_price_available
                          ? `✅ ${t.currentAgmarknet}`
                          : `⚪ ${t.noPrice}`}

                      </span>

                    </div>

                  ),
                )}

              </div>

            </div>
          )}

      </section>


      {/* =================================================
          FOOTER
      ================================================= */}

      <footer>

        <strong>
          🌾 CropConn8t
        </strong>

        <span>
          {t.footer}
        </span>

      </footer>


      {/* =================================================
          LOCATION MODAL
      ================================================= */}

      {locationModal && (

        <div
          className="location-modal-backdrop"
          onClick={(event) => {

            if (
              event.target ===
              event.currentTarget
            ) {
              setLocationModal(false);
              setManualMode(false);
              setLocationError("");
            }

          }}
        >

          <div className="location-modal">

            <div className="location-modal-icon">
              📍
            </div>

            <h2>
              {t.chooseLocation}
            </h2>

            <p>
              {t.locationDescription}
            </p>


            {!manualMode ? (

              <>
                <button
                  className="location-primary-button"
                  onClick={
                    detectLocation
                  }
                  disabled={
                    locationLoading
                  }
                >
                  📍{" "}
                  {locationLoading
                    ? t.detecting
                    : t.useMyLocation}
                </button>

                <button
                  className="location-secondary-button"
                  onClick={() => {
                    setManualMode(
                      true,
                    );
                    setLocationError(
                      "",
                    );
                  }}
                >
                  🔎{" "}
                  {t.chooseAnother}
                </button>
              </>

            ) : (

              <>

                {/* DISTRICT */}

                <div className="field">

                  <label>
                    {t.chooseDistrict}
                  </label>

                  <select
                    value={districtId}
                    onChange={async (
                      event,
                    ) => {

                      const selected =
                        districts.find(
                          (item) =>
                            String(
                              item.district_id,
                            ) ===
                            event.target
                              .value,
                        );

                      const nextId =
                        event.target
                          .value;

                      const nextName =
                        selected?.district_name ||
                        "";

                      setDistrictId(
                        nextId,
                      );

                      setDistrictName(
                        nextName,
                      );

                      setLocation(
                        null,
                      );

                      setPriceData(
                        null,
                      );

                      await loadTowns(
                        nextId,
                        nextName,
                      );
                    }}
                  >

                    <option value="">
                      {t.chooseDistrict}
                    </option>

                    {districts.map(
                      (item) => (
                        <option
                          key={
                            item.district_id
                          }
                          value={
                            item.district_id
                          }
                        >
                          {
                            item.district_name
                          }
                        </option>
                      ),
                    )}

                  </select>

                </div>


                {/* MANDAL */}

                <div className="field">

                  <label>
                    {t.chooseTown}
                  </label>

                  <select
                    disabled={
                      !districtId ||
                      townLoading
                    }
                    value={townCode}
                    onChange={async (
                      event,
                    ) => {

                      const selected =
                        towns.find(
                          (item) =>
                            item.id ===
                            event.target
                              .value,
                        );

                      const nextCode =
                        event.target
                          .value;

                      setTownCode(
                        nextCode,
                      );

                      setTownName(
                        selected?.town_name ||
                          "",
                      );

                      setLocation(
                        null,
                      );

                      setPriceData(
                        null,
                      );

                      await loadVillages(
                        nextCode,
                      );
                    }}
                  >

                    <option value="">
                      {townLoading
                        ? "Loading mandals..."
                        : t.chooseTown}
                    </option>

                    {towns.map(
                      (item) => (
                        <option
                          key={item.id}
                          value={item.id}
                        >
                          {item.town_name} (
                          {
                            item.village_count
                          }
                          )
                        </option>
                      ),
                    )}

                  </select>

                </div>


                {/* VILLAGE */}

                <div className="field">

                  <label>
                    {t.chooseVillage}
                  </label>

                  <select
                    disabled={
                      !townCode ||
                      villageLoading
                    }
                    value={
                      villageCode
                    }
                    onChange={(event) => {

                      const selected =
                        villages.find(
                          (item) =>
                            item.village_code ===
                            event.target
                              .value,
                        );

                      setVillageCode(
                        event.target
                          .value,
                      );

                      setVillageName(
                        selected?.village_name ||
                          "",
                      );

                      setLocation(
                        null,
                      );

                      setPriceData(
                        null,
                      );

                    }}
                  >

                    <option value="">
                      {villageLoading
                        ? "Loading villages..."
                        : t.chooseVillage}
                    </option>

                    {villages.map(
                      (item) => (
                        <option
                          key={
                            item.village_code
                          }
                          value={
                            item.village_code
                          }
                        >
                          {
                            item.village_name
                          }

                          {item.pincode
                            ? ` — ${item.pincode}`
                            : ""}
                        </option>
                      ),
                    )}

                  </select>

                </div>


                {/* USE SELECTED */}

                <button
                  className="location-primary-button"
                  onClick={
                    geocodeSelection
                  }
                  disabled={
                    manualLoading ||
                    (
                      !districtName &&
                      !townName &&
                      !villageName
                    )
                  }
                >
                  {manualLoading
                    ? t.findingLocation
                    : `✓ ${t.findLocation}`}
                </button>


                {/* SEARCH */}

                <input
                  className="location-input"
                  value={search}
                  onChange={(event) =>
                    setSearch(
                      event.target.value,
                    )
                  }
                  placeholder={
                    t.exampleLocation
                  }
                  onKeyDown={(event) => {

                    if (
                      event.key ===
                        "Enter" &&
                      search.trim()
                    ) {
                      chooseManual(
                        search.trim(),
                      );
                    }

                  }}
                />


                <button
                  className="location-secondary-button"
                  onClick={() => {
                    setManualMode(
                      false,
                    );
                    setLocationError(
                      "",
                    );
                  }}
                >
                  ← {t.back}
                </button>

              </>
            )}


            {locationError && (
              <div className="location-error">
                {locationError}
              </div>
            )}


            <button
              className="location-close-button"
              onClick={() => {
                setLocationModal(
                  false,
                );
                setManualMode(
                  false,
                );
                setLocationError(
                  "",
                );
              }}
            >
              {t.close}
            </button>

          </div>

        </div>
      )}

    </div>
  );
}