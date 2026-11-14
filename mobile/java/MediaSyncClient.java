package com.appleupscaler.studio.remote;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;

/**
 * Cross-platform Java Remote Render Client
 */
public class MediaSyncClient {
    private final String hostname;
    private final int port;
    private Socket clientSocket;
    private PrintWriter out;
    private BufferedReader in;

    public MediaSyncClient(String hostname, int port) {
        this.hostname = hostname;
        this.port = port;
    }

    public boolean startConnection() {
        try {
            clientSocket = new Socket(hostname, port);
            out = new PrintWriter(clientSocket.getOutputStream(), true);
            in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
            return true;
        } catch (Exception e) {
            System.err.println("Connection error: " + e.getMessage());
            return false;
        }
    }

    public String sendCommand(String command) {
        try {
            out.println(command);
            return in.readLine();
        } catch (Exception e) {
            return "ERROR: " + e.getMessage();
        }
    }

    public void stopConnection() {
        try {
            if (in != null) in.close();
            if (out != null) out.close();
            if (clientSocket != null) clientSocket.close();
        } catch (Exception ignored) {}
    }
}
