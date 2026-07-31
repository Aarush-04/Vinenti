import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { View, ActivityIndicator, SafeAreaView } from "react-native";
import Svg, { Path } from "react-native-svg";
import {
  useFonts as useFraunces,
  Fraunces_600SemiBold,
  Fraunces_500Medium_Italic,
} from "@expo-google-fonts/fraunces";
import {
  Manrope_400Regular,
  Manrope_600SemiBold,
  Manrope_700Bold,
} from "@expo-google-fonts/manrope";
import {
  IBMPlexMono_400Regular,
  IBMPlexMono_500Medium,
} from "@expo-google-fonts/ibm-plex-mono";

import { COLORS, TrunkMark } from "./theme";
import { PreferencesProvider } from "./PreferencesContext";
import TodayScreen from "./screens/TodayScreen";
import ChatScreen from "./screens/ChatScreen";
import SettingsScreen from "./screens/SettingsScreen";

const Tab = createBottomTabNavigator();

function ChatIcon({ color }) {
  return (
    <Svg width={20} height={20} viewBox="0 0 24 24" fill="none">
      <Path
        d="M4 5h16v11H9l-4 4V5z"
        stroke={color}
        strokeWidth={2}
        strokeLinejoin="round"
        fill="none"
      />
    </Svg>
  );
}

function SettingsIcon({ color }) {
  return (
    <Svg width={20} height={20} viewBox="0 0 24 24" fill="none">
      <Path
        d="M4 7h16M4 12h16M4 17h16"
        stroke={color}
        strokeWidth={2}
        strokeLinecap="round"
      />
    </Svg>
  );
}

export default function App() {
  const [fontsLoaded] = useFraunces({
    Fraunces_600SemiBold,
    Fraunces_500Medium_Italic,
    Manrope_400Regular,
    Manrope_600SemiBold,
    Manrope_700Bold,
    IBMPlexMono_400Regular,
    IBMPlexMono_500Medium,
  });

  if (!fontsLoaded) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.ink, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator color={COLORS.ember} size="large" />
      </SafeAreaView>
    );
  }

  return (
    <PreferencesProvider>
      <NavigationContainer>
        <Tab.Navigator
          screenOptions={{
            headerShown: false,
            tabBarStyle: { backgroundColor: COLORS.ink, borderTopColor: COLORS.hairline },
            tabBarActiveTintColor: COLORS.ember,
            tabBarInactiveTintColor: COLORS.muted,
            tabBarLabelStyle: { fontFamily: "Manrope_600SemiBold", fontSize: 11 },
          }}
        >
          <Tab.Screen
            name="Today"
            component={TodayScreen}
            options={{ tabBarIcon: ({ color }) => <TrunkMark size={20} color={color} /> }}
          />
          <Tab.Screen
            name="Chat"
            component={ChatScreen}
            options={{ tabBarIcon: ({ color }) => <ChatIcon color={color} /> }}
          />
          <Tab.Screen
            name="Settings"
            component={SettingsScreen}
            options={{ tabBarIcon: ({ color }) => <SettingsIcon color={color} /> }}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </PreferencesProvider>
  );
}