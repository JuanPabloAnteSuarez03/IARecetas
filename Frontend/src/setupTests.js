import '@testing-library/jest-dom';
import { jest } from '@jest/globals';

// ── Mock Firebase Auth ─────────────────────────────────────
const mockUser = { uid: 'test-uid-123', displayName: 'Test User', email: 'test@example.com' };

jest.mock('./firebase', () => ({
  auth: {
    currentUser: mockUser,
  },
  db: {},
  googleProvider: {},
}));

// ── Mock Firebase Firestore ────────────────────────────────
jest.mock('firebase/firestore', () => ({
  collection: jest.fn(() => 'mock-collection-ref'),
  addDoc:     jest.fn(() => Promise.resolve({ id: 'mock-doc-id' })),
  getDocs:    jest.fn(() => Promise.resolve({ docs: [] })),
  doc:        jest.fn(() => 'mock-doc-ref'),
  deleteDoc:  jest.fn(() => Promise.resolve()),
  updateDoc:  jest.fn(() => Promise.resolve()),
  getFirestore: jest.fn(),
}));

// ── Mock Firebase Auth module ──────────────────────────────
jest.mock('firebase/auth', () => ({
  getAuth:           jest.fn(),
  GoogleAuthProvider: jest.fn().mockImplementation(() => ({})),
  signInWithPopup:   jest.fn(),
  signOut:           jest.fn(() => Promise.resolve()),
  onAuthStateChanged: jest.fn((auth, callback) => {
    callback(mockUser);
    return jest.fn(); // unsubscribe fn
  }),
}));

// ── Mock Firebase App ──────────────────────────────────────
jest.mock('firebase/app', () => ({
  initializeApp: jest.fn(() => ({})),
}));

// ── Mock window.matchMedia ────────────────────────────────
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});