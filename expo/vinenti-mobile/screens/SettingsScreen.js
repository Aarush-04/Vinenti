import React from "react";
import { SafeAreaView, View, Text, TouchableOpacity, StyleSheet, ScrollView } from "react-native";
import { COLORS } from "../theme";
import { usePreferences } from "../PreferencesContext";

const LENGTH_OPTIONS = [
  { key: "short", label: "Short", desc: "Just the essentials — one or two lines." },
  { key: "medium", label: "Medium", desc: "Momentum read plus what matters most today." },
  { key: "long", label: "Long", desc: "Full detail, including inbox context and reasoning." },
];

const TONE_OPTIONS = [
  { key: "encouraging", label: "Encouraging", desc: "Warm, supportive, softens the misses." },
  { key: "balanced", label: "Balanced", desc: "Calm and direct, honest without harshness." },
  { key: "firm", label: "Firm", desc: "Accountability-focused — calls out gaps plainly." },
];

function OptionRow({ option, selected, onPress }) {
  return (
    <TouchableOpacity
      style={[styles.optionRow, selected && styles.optionRowSelected]}
      onPress={onPress}
    >
      <View style={{ flex: 1 }}>
        <Text style={styles.optionLabel}>{option.label}</Text>
        <Text style={styles.optionDesc}>{option.desc}</Text>
      </View>
      <View style={[styles.radio, selected && styles.radioSelected]} />
    </TouchableOpacity>
  );
}

export default function SettingsScreen() {
  const { preferences, updatePreferences } = usePreferences();

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>Settings</Text>

        <Text style={styles.eyebrow}>Briefing length</Text>
        {LENGTH_OPTIONS.map((opt) => (
          <OptionRow
            key={opt.key}
            option={opt}
            selected={preferences.length === opt.key}
            onPress={() => updatePreferences({ length: opt.key })}
          />
        ))}

        <View style={styles.hairline} />

        <Text style={styles.eyebrow}>Companion tone</Text>
        {TONE_OPTIONS.map((opt) => (
          <OptionRow
            key={opt.key}
            option={opt}
            selected={preferences.tone === opt.key}
            onPress={() => updatePreferences({ tone: opt.key })}
          />
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.ink },
  scroll: { padding: 24, paddingBottom: 60 },
  title: { fontFamily: "Fraunces_600SemiBold", color: COLORS.parchment, fontSize: 26, marginBottom: 24 },
  eyebrow: {
    fontFamily: "Manrope_700Bold",
    color: COLORS.ember,
    fontSize: 11,
    letterSpacing: 2,
    textTransform: "uppercase",
    marginBottom: 12,
  },
  hairline: { height: 1, backgroundColor: COLORS.hairline, marginVertical: 24 },
  optionRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.card,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
  },
  optionRowSelected: { borderWidth: 1, borderColor: COLORS.ember },
  optionLabel: { fontFamily: "Manrope_600SemiBold", color: COLORS.parchment, fontSize: 15, marginBottom: 3 },
  optionDesc: { fontFamily: "Manrope_400Regular", color: COLORS.muted, fontSize: 12 },
  radio: { width: 18, height: 18, borderRadius: 9, borderWidth: 2, borderColor: COLORS.muted },
  radioSelected: { borderColor: COLORS.ember, backgroundColor: COLORS.ember },
});
