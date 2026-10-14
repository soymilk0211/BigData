// All Firebase access lives here; the UI never touches Firestore directly.
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import {
  getFirestore, collection, addDoc, updateDoc, deleteDoc, doc,
  query, orderBy, onSnapshot, serverTimestamp,
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";
import { firebaseConfig } from "./firebase-config.js";

export const isConfigured = !Object.values(firebaseConfig).some((v) => String(v).includes("YOUR_"));

const COLLECTION = "messages";
let messages = null;

if (isConfigured) {
  messages = collection(getFirestore(initializeApp(firebaseConfig)), COLLECTION);
}

function requireDb() {
  if (!messages) throw new Error("Firebase is not configured (see firebase-config.js).");
  return messages;
}

export function addMessage(name, text) {
  return addDoc(requireDb(), { name, text, createdAt: serverTimestamp(), updatedAt: null });
}

export function updateMessage(id, text) {
  requireDb();
  return updateDoc(doc(messages, id), { text, updatedAt: serverTimestamp() });
}

export function deleteMessage(id) {
  requireDb();
  return deleteDoc(doc(messages, id));
}

// Calls onChange(list) now and on every change; returns an unsubscribe function.
export function watchMessages(onChange, onError) {
  const q = query(requireDb(), orderBy("createdAt", "desc"));
  return onSnapshot(
    q,
    (snap) => onChange(snap.docs.map((d) => ({ id: d.id, ...d.data() }))),
    onError,
  );
}
