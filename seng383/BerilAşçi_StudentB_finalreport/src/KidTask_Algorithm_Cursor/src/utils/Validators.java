package utils;

public class Validators {
    public static boolean isNullOrEmpty(String value) {
        return value == null || value.trim().isEmpty();
    }

    public static int parsePositiveInt(String value, int defaultValue) {
        try {
            int v = Integer.parseInt(value);
            return v > 0 ? v : defaultValue;
        } catch (NumberFormatException ex) {
            return defaultValue;
        }
    }
}


