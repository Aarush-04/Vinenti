import React, { useState } from "react";
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
import { COLORS, TrunkMark, API_BASE_URL } from "../theme";
import { usePreferences } from "../PreferencesContext";

export default function ChatScreen() {
  const { preferences } = usePreferences();
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);

  const sendMessage = async () => {
    if (!chatInput.trim()) return;
    const userMsg = { role: "user", text: chatInput };
    const historyForApi = messages.map((m) => ({
      role: m.role === "user" ? "user" : "assistant",
      content: m.text,
    }));
    setMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setSending(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg.text,
          history: historyForApi,
          tone: preferences.tone,
        }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "ai", text: data.reply }]);
    } catch (e) {
      setMessages((prev) => [...prev, { role: "ai", text: "Couldn't reach the server just now." }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <View style={styles.header}>
          <Text style={styles.title}>Talk to Vinenti</Text>
        </View>
        <ScrollView contentContainerStyle={styles.scroll}>
          {messages.length === 0 && (
            <Text style={styles.empty}>Ask about today, your GitHub streak, or what's coming up.</Text>
          )}
          {messages.map((m, i) => (
            <View key={i} style={[styles.bubble, m.role === "user" ? styles.userBubble : styles.aiBubble]}>
              <Text style={m.role === "user" ? styles.userBubbleText : styles.aiBubbleText}>{m.text}</Text>
            </View>
          ))}
          {sending && <ActivityIndicator color={COLORS.ember} style={{ marginTop: 8 }} />}
        </ScrollView>
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            placeholder="Talk to your companion..."
            placeholderTextColor={COLORS.muted}
            value={chatInput}
            onChangeText={setChatInput}
            onSubmitEditing={sendMessage}
          />
          <TouchableOpacity style={styles.sendButton} onPress={sendMessage}>
            <TrunkMark size={16} color={COLORS.ink} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.ink },
  header: { paddingHorizontal: 24, paddingTop: 20, paddingBottom: 12 },
  title: { fontFamily: "Fraunces_600SemiBold", color: COLORS.parchment, fontSize: 22 },
  scroll: { padding: 24, paddingTop: 8, flexGrow: 1 },
  empty: { fontFamily: "Manrope_400Regular", color: COLORS.muted, fontSize: 13, fontStyle: "italic" },
  bubble: { padding: 12, borderRadius: 14, marginBottom: 10, maxWidth: "85%" },
  userBubble: { backgroundColor: COLORS.ember, alignSelf: "flex-end" },
  aiBubble: { backgroundColor: COLORS.card, alignSelf: "flex-start" },
  userBubbleText: { fontFamily: "Manrope_400Regular", color: COLORS.ink, fontSize: 14 },
  aiBubbleText: { fontFamily: "Manrope_400Regular", color: COLORS.parchment, fontSize: 14 },
  inputRow: {
    flexDirection: "row",
    padding: 14,
    backgroundColor: COLORS.ink,
    borderTopWidth: 1,
    borderTopColor: COLORS.hairline,
    alignItems: "center",
  },
  input: {
    flex: 1,
    fontFamily: "Manrope_400Regular",
    backgroundColor: COLORS.card,
    color: COLORS.parchment,
    borderRadius: 22,
    paddingHorizontal: 18,
    paddingVertical: 12,
    marginRight: 10,
    fontSize: 14,
  },
  sendButton: {
    backgroundColor: COLORS.ember,
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
  },
});
