package utils;

import javax.swing.JOptionPane;

public class ErrorHandler {
    public static void log(String message) {
        System.err.println(message);
    }

    public static void show(String message) {
        JOptionPane.showMessageDialog(null, message, "KidTask Error", JOptionPane.ERROR_MESSAGE);
    }
}


