# LiveKit and SIP

LiveKit is intentionally not enabled in the default Compose stack. It needs a chosen Indian SIP provider, public UDP/TCP media ports, TURN configuration, and provider credentials.

Add it after the web/WhatsApp pilot has working business actions. The voice agent must call the API's guarded-action endpoint; it must not write to PostgreSQL directly.

