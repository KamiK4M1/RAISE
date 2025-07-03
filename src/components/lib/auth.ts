import type { NextAuthOptions } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"
import GoogleProvider from "next-auth/providers/google"
import { MongoDBAdapter } from "@auth/mongodb-adapter"
import { PrismaAdapter } from "@auth/prisma-adapter"
import { MongoClient } from "mongodb"
import prisma from "@/lib/prisma" 
import bcrypt from "bcryptjs"

// Extend NextAuth types to include id in session
declare module "next-auth" {
  interface Session {
    accessToken?: string;
    user: {
      id: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
    };
  }
  
  interface User {
    id: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
    accessToken?: string;
  }
}

const client = new MongoClient(process.env.MONGODB_URI!)
const clientPromise = client.connect()

export const authOptions: NextAuthOptions = {
  // Use MongoDB adapter (commented out Prisma)
  // adapter: PrismaAdapter(prisma),
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }

        try {
          console.log("Attempting to log in with credentials:", credentials.email);
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
          const backendResponse = await fetch(`${apiUrl}/api/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email: credentials.email, password: credentials.password }),
          });

          console.log("Backend response status:", backendResponse.status);
          if (!backendResponse.ok) {
            const errorData = await backendResponse.json().catch(() => ({ message: "Unknown error" }));
            console.error("Backend login failed:", backendResponse.status, errorData);
            return null;
          }

          const data = await backendResponse.json();
          console.log("Backend login successful, received data:", data);
          
          if (data.access_token && data.user) {
            console.log("Returning user object to NextAuth:", { id: data.user.id, email: data.user.email, name: data.user.name, accessToken: data.access_token });
            return {
              id: data.user.id,
              email: data.user.email,
              name: data.user.name,
              accessToken: data.access_token,
            };
          } else {
            console.error("Backend login response missing expected data:", data);
            return null;
          }
        } catch (error) {
          console.error("Error during backend authentication:", error);
          return null;
        }
      },
    }),
  ],
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id
        if ((user as any).accessToken) {
          token.accessToken = (user as any).accessToken
        }
      }
      return token
    },
    async session({ session, token }) {
      if (token && session.user) {
        session.user.id = token.id
        session.accessToken = token.accessToken
      }
      return session
    },
  },
}
