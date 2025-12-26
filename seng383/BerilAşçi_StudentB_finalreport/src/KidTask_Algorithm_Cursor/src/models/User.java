package models;

import java.util.UUID;

public class User {
    private final String id;
    private String username;
    private String password;
    private int points;
    private int level;

    public User(String id, String username, String password, int points, int level) {
        this.id = id;
        this.username = username;
        this.password = password;
        this.points = points;
        this.level = level;
    }

    public User(String username, String password) {
        this(UUID.randomUUID().toString(), username, password, 0, 1);
    }

    public String getId() {
        return id;
    }

    public String getUsername() {
        return username;
    }

    public String getPassword() {
        return password;
    }

    public int getPoints() {
        return points;
    }

    public int getLevel() {
        return level;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public void addPoints(int value) {
        this.points += value;
        if (this.points < 0) {
            this.points = 0;
        }
    }

    public void setLevel(int level) {
        this.level = Math.max(1, level);
    }

    public String toStorageString() {
        return String.join("|",
                id,
                escape(username),
                escape(password),
                String.valueOf(points),
                String.valueOf(level));
    }

    public static User fromStorageString(String line) {
        try {
            String[] parts = line.split("\\|", -1);
            if (parts.length < 5) {
                return null;
            }
            String id = parts[0];
            String username = unescape(parts[1]);
            String password = unescape(parts[2]);
            int points = Integer.parseInt(parts[3]);
            int level = Integer.parseInt(parts[4]);
            return new User(id, username, password, points, level);
        } catch (Exception ex) {
            return null;
        }
    }

    private static String escape(String value) {
        return value.replace("|", "\\|");
    }

    private static String unescape(String value) {
        return value.replace("\\|", "|");
    }
}


