import React, { useState, useEffect, useCallback } from "react";
import {
  SafeAreaView,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from "react-native";

// Change this to your PC's local IP address (see README_MOBILE.md).
// Both your phone and PC must be on the same WiFi network.
const API_BASE_URL = "http://192.168.1.100:5000";

export default function App() {
  const [loading, setLoading] = useState(true);
  const [brief, setBrief] = useState("");
  const [githubSummary, setGithubSummary] = useState("");
  const [calendarSummary, setCalendarSummary] = useState("");
  const [error, setError] = useState(null);

  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);

  const fetchBrief = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/brief`);
      const data = await res.json();
      setBrief(data.brief);
      setGithubSummary(data.github);
      setCalendarSummary(data.calendar);
    } catch (e) {
      setError(
        "Couldn't reach the server. Make sure api_server.py is running " +
          "on your PC and your phone is on the same WiFi network."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBrief();
  }, [fetchBrief]);

  const sendMessage = async () => {
    if (!chatInput.trim()) return;
    const userMsg = { role: "user", text: chatInput };
    setMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setSending(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.text }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "ai", text: data.reply }]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: "Couldn't reach the server just now." },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView contentContainerStyle={styles.scroll}>
          <Text style={styles.header}>Vinenti</Text>
          <Text style={styles.subheader}>Your daily brief</Text>

          {loading && <ActivityIndicator size="large" style={{ marginTop: 20 }} />}

          {error && <Text style={styles.error}>{error}</Text>}

          {!loading && !error && (
            <View style={styles.card}>
              <Text style={styles.briefText}>{brief}</Text>
              <View style={styles.divider} />
              <Text style={styles.meta}>GitHub: {githubSummary}</Text>
              <Text style={styles.meta}>Calendar: {calendarSummary}</Text>
            </View>
          )}

          <TouchableOpacity style={styles.refreshButton} onPress={fetchBrief}>
            <Text style={styles.refreshButtonText}>Refresh brief</Text>
          </TouchableOpacity>

          <Text style={styles.chatHeader}>Chat</Text>
          <View style={styles.chatBox}>
            {messages.map((m, i) => (
              <View
                key={i}
                style={[
                  styles.bubble,
                  m.role === "user" ? styles.userBubble : styles.aiBubble,
                ]}
              >
                <Text style={styles.bubbleText}>{m.text}</Text>
              </View>
            ))}
            {sending && <ActivityIndicator style={{ marginTop: 8 }} />}
          </View>
        </ScrollView>

        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            placeholder="Talk to your companion..."
            value={chatInput}
            onChangeText={setChatInput}
            onSubmitEditing={sendMessage}
          />
          <TouchableOpacity style={styles.sendButton} onPress={sendMessage}>
            <Text style={styles.sendButtonText}>Send</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#101418" },
  scroll: { padding: 20, paddingBottom: 100 },
  header: { fontSize: 28, fontWeight: "700", color: "#fff" },
  subheader: { fontSize: 14, color: "#9aa5b1", marginBottom: 16 },
  card: {
    backgroundColor: "#1b2129",
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  briefText: { color: "#e8ebef", fontSize: 15, lineHeight: 22 },
  divider: { height: 1, backgroundColor: "#2a323d", marginVertical: 12 },
  meta: { color: "#7d8791", fontSize: 12, marginBottom: 4 },
  error: { color: "#e57373", marginTop: 16 },
  refreshButton: {
    backgroundColor: "#2a323d",
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: "center",
    marginBottom: 24,
  },
  refreshButtonText: { color: "#fff", fontWeight: "600" },
  chatHeader: { color: "#9aa5b1", fontSize: 14, marginBottom: 8 },
  chatBox: { minHeight: 100 },
  bubble: { padding: 10, borderRadius: 12, marginBottom: 8, maxWidth: "85%" },
  userBubble: { backgroundColor: "#3a6df0", alignSelf: "flex-end" },
  aiBubble: { backgroundColor: "#1b2129", alignSelf: "flex-start" },
  bubbleText: { color: "#fff" },
  inputRow: {
    flexDirection: "row",
    padding: 12,
    backgroundColor: "#161b21",
    alignItems: "center",
  },
  input: {
    flex: 1,
    backgroundColor: "#232a33",
    color: "#fff",
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginRight: 8,
  },
  sendButton: {
    backgroundColor: "#3a6df0",
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
  },
  sendButtonText: { color: "#fff", fontWeight: "600" },
});
