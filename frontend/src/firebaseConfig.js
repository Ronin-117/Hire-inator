// src/firebaseConfig.js

import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// Your web app's Firebase configuration
const firebaseConfig = {
            apiKey: "AIzaSyAbCTUKZKxEC66mzA_NBWDhfLhJbNplad8",
            authDomain: "hire-inator.firebaseapp.com",
            projectId: "hire-inator",
            storageBucket: "hire-inator.appspot.com",
            messagingSenderId: "992353030727",
            appId: "1:992353030727:web:4f1085576a66a233061762",
            measurementId: "G-RY888QL03S"
        };

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
export const db = getFirestore(app);