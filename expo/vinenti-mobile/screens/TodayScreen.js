import React, { useState, useEffect, useCallback } from "react";
import {
  SafeAreaView,
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from "react-native";
import { COLORS, TrunkMark, getGreeting, API_BASE_URL } from "../theme";
import { usePreferences } from "../PreferencesContext";

function Eyebrow({ children }) {
  return <Text style={styles.eyebrow}>{children}</Text>;
}

function ScheduleRow({ item }) {
  return (
    <View style={styles.scheduleRow}>
      <View style={[styles.dot, item.label === "Today" ? styles.dotToday : styles.dotTomorrow]} />
      <View style={{ flex: 1 }}>
        <Text style={styles.scheduleTime}>
          {item.label}
          {item.time ? ` · ${item.time}` : " · All day"}
        </Text>
        <Text style={styles.scheduleSummary}>{item.summary}</Text>
      </View>
    </View>
  );
}

function TaskChip({ title, variant }) {
  const bg =
    variant === "overdue" ? COLORS.rust : variant === "today" ? COLORS.ember : COLORS.moss;
  return (
    <View style={[styles.chip, { backgroundColor: bg }]}>
      <Text style={styles.chipText} numberOfLines={1}>
        {title}
      </Text>
    </View>
  );
}

export default function TodayScreen() {
  const { preferences, loaded } = usePreferences();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const fetchBrief = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        length: preferences.length,
        tone: preferences.tone,
      });
      const res = await fetch(`${API_BASE_URL}/api/brief?${params.toString()}`);
      const json = await res.json();
      setData(json);
    } catch (e) {
      setError(
        "Couldn't reach the server. Make sure api_server.py is running and your phone is on the same WiFi."
      );
    } finally {
      setLoading(false);
    }
  }, [preferences.length, preferences.tone]);

  useEffect(() => {
    if (loaded) fetchBrief();
  }, [loaded, fetchBrief]);

  const now = new Date();
  const dateLabel = now
    .toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })
    .toUpperCase();

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.header}>
          <View style={styles.wordmarkRow}>
            <TrunkMark size={20} />
            <Text style={styles.wordmark}>vinenti</Text>
          </View>
          <Text style={styles.greeting}>{getGreeting()}, Aarush.</Text>
          <Text style={styles.dateLabel}>{dateLabel}</Text>
        </View>

        {(loading || !loaded) && <ActivityIndicator color={COLORS.ember} style={{ marginTop: 32 }} />}
        {error && <Text style={styles.error}>{error}</Text>}

        {!loading && loaded && !error && data && (
          <>
            <View style={styles.section}>
              <Eyebrow>Briefing</Eyebrow>
              <Text style={styles.narrative}>{data.narrative}</Text>
              <View style={styles.hairline} />
            </View>

            {data.schedule?.length > 0 && (
              <View style={styles.section}>
                <Eyebrow>Schedule</Eyebrow>
                {data.schedule.map((item, i) => (
                  <ScheduleRow key={i} item={item} />
                ))}
                <View style={styles.hairline} />
              </View>
            )}

            {(data.tasks?.overdue.length > 0 ||
              data.tasks?.today.length > 0 ||
              data.tasks?.tomorrow.length > 0) && (
              <View style={styles.section}>
                <Eyebrow>Tasks</Eyebrow>
                <View style={styles.chipRow}>
                  {data.tasks.overdue.map((t, i) => (
                    <TaskChip key={`o${i}`} title={t} variant="overdue" />
                  ))}
                  {data.tasks.today.map((t, i) => (
                    <TaskChip key={`t${i}`} title={t} variant="today" />
                  ))}
                  {data.tasks.tomorrow.map((t, i) => (
                    <TaskChip key={`m${i}`} title={t} variant="tomorrow" />
                  ))}
                </View>
                <View style={styles.hairline} />
              </View>
            )}

            <View style={styles.section}>
              <Eyebrow>GitHub</Eyebrow>
              <Text style={styles.metaLine}>
                {data.github?.commit_count > 0
                  ? `${data.github.commit_count} commit(s) in the last 24h`
                  : "No commits in the last 24 hours"}
              </Text>
              {data.github?.commits?.slice(0, 3).map((c, i) => (
                <Text key={i} style={styles.mono}>
                  {c.repo} — {c.message}
                </Text>
              ))}
              <View style={styles.hairline} />
            </View>

            {data.inbox?.length > 0 && (
              <View style={styles.section}>
                <Eyebrow>Inbox</Eyebrow>
                {data.inbox.slice(0, 4).map((m, i) => (
                  <View key={i} style={styles.inboxCard}>
                    <Text style={styles.inboxSubject} numberOfLines={1}>
                      {m.subject}
                    </Text>
                    <Text style={styles.inboxSender} numberOfLines={1}>
                      {m.sender}
                    </Text>
                  </View>
                ))}
                <View style={styles.hairline} />
              </View>
            )}

            <View style={styles.section}>
              <Eyebrow>Weather</Eyebrow>
              <Text style={styles.metaLine}>{data.weather?.text}</Text>
            </View>

            <TouchableOpacity style={styles.refreshButton} onPress={fetchBrief}>
              <TrunkMark size={16} color={COLORS.ink} />
              <Text style={styles.refreshButtonText}>Refresh</Text>
            </TouchableOpacity>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.ink },
  scroll: { padding: 24, paddingBottom: 60 },

  header: { marginBottom: 28 },
  wordmarkRow: { flexDirection: "row", alignItems: "center", marginBottom: 18, gap: 8 },
  wordmark: {
    fontFamily: "Manrope_700Bold",
    color: COLORS.muted,
    fontSize: 13,
    letterSpacing: 3,
    textTransform: "uppercase",
  },
  greeting: { fontFamily: "Fraunces_600SemiBold", color: COLORS.parchment, fontSize: 28, marginBottom: 6 },
  dateLabel: { fontFamily: "IBMPlexMono_400Regular", color: COLORS.muted, fontSize: 12, letterSpacing: 1.5 },

  section: { marginBottom: 4 },
  eyebrow: {
    fontFamily: "Manrope_700Bold",
    color: COLORS.ember,
    fontSize: 11,
    letterSpacing: 2,
    textTransform: "uppercase",
    marginBottom: 10,
  },
  hairline: { height: 1, backgroundColor: COLORS.hairline, marginTop: 18, marginBottom: 18 },

  narrative: { fontFamily: "Manrope_400Regular", color: COLORS.parchment, fontSize: 16, lineHeight: 24 },
  error: { fontFamily: "Manrope_400Regular", color: COLORS.rust, marginTop: 20 },

  scheduleRow: { flexDirection: "row", marginBottom: 12, alignItems: "flex-start" },
  dot: { width: 8, height: 8, borderRadius: 4, marginTop: 6, marginRight: 12 },
  dotToday: { backgroundColor: COLORS.ember },
  dotTomorrow: { backgroundColor: COLORS.moss },
  scheduleTime: { fontFamily: "IBMPlexMono_500Medium", color: COLORS.muted, fontSize: 11, marginBottom: 2 },
  scheduleSummary: { fontFamily: "Manrope_600SemiBold", color: COLORS.parchment, fontSize: 15 },

  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, maxWidth: "100%" },
  chipText: { fontFamily: "Manrope_600SemiBold", color: COLORS.ink, fontSize: 12 },

  metaLine: { fontFamily: "Manrope_400Regular", color: COLORS.parchment, fontSize: 14, marginBottom: 6 },
  mono: { fontFamily: "IBMPlexMono_400Regular", color: COLORS.muted, fontSize: 11, marginBottom: 4 },

  inboxCard: { backgroundColor: COLORS.card, borderRadius: 10, padding: 12, marginBottom: 8 },
  inboxSubject: { fontFamily: "Manrope_600SemiBold", color: COLORS.parchment, fontSize: 13, marginBottom: 2 },
  inboxSender: { fontFamily: "IBMPlexMono_400Regular", color: COLORS.muted, fontSize: 11 },

  refreshButton: {
    flexDirection: "row",
    gap: 8,
    backgroundColor: COLORS.ember,
    paddingVertical: 12,
    borderRadius: 24,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 12,
  },
  refreshButtonText: { fontFamily: "Manrope_600SemiBold", color: COLORS.ink, fontSize: 13 },
});
