import React, { createContext, useContext, useState, useEffect } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";

const PreferencesContext = createContext(null);

const DEFAULTS = { length: "medium", tone: "balanced" };
const STORAGE_KEY = "vinenti_preferences";

export function PreferencesProvider({ children }) {
  const [preferences, setPreferences] = useState(DEFAULTS);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((stored) => {
        if (stored) setPreferences(JSON.parse(stored));
      })
      .finally(() => setLoaded(true));
  }, []);

  const updatePreferences = async (next) => {
    const merged = { ...preferences, ...next };
    setPreferences(merged);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
  };

  return (
    <PreferencesContext.Provider value={{ preferences, updatePreferences, loaded }}>
      {children}
    </PreferencesContext.Provider>
  );
}

export function usePreferences() {
  return useContext(PreferencesContext);
}
