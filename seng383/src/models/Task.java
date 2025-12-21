package models;

import java.time.LocalDate;
import java.util.UUID;

public class Task {
    private final String id;
    private String title;
    private String description;
    private Frequency frequency;
    private int points;
    private boolean completed;
    private LocalDate createdDate;

    public enum Frequency {
        DAILY,
        WEEKLY
    }

    public Task(String id, String title, String description, Frequency frequency, int points,
                boolean completed, LocalDate createdDate) {
        this.id = id;
        this.title = title;
        this.description = description;
        this.frequency = frequency;
        this.points = points;
        this.completed = completed;
        this.createdDate = createdDate;
    }

    public Task(String title, String description, Frequency frequency, int points) {
        this(UUID.randomUUID().toString(), title, description, frequency, points, false, LocalDate.now());
    }

    public String getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public String getDescription() {
        return description;
    }

    public Frequency getFrequency() {
        return frequency;
    }

    public int getPoints() {
        return points;
    }

    public boolean isCompleted() {
        return completed;
    }

    public LocalDate getCreatedDate() {
        return createdDate;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public void setFrequency(Frequency frequency) {
        this.frequency = frequency;
    }

    public void setPoints(int points) {
        this.points = points;
    }

    public void markCompleted() {
        this.completed = true;
    }

    public String toStorageString() {
        return String.join("|",
                id,
                escape(title),
                escape(description),
                frequency.name(),
                String.valueOf(points),
                String.valueOf(completed),
                createdDate.toString());
    }

    public static Task fromStorageString(String line) {
        try {
            String[] parts = line.split("\\|", -1);
            if (parts.length < 7) {
                return null;
            }
            String id = parts[0];
            String title = unescape(parts[1]);
            String desc = unescape(parts[2]);
            Frequency freq = Frequency.valueOf(parts[3]);
            int pts = Integer.parseInt(parts[4]);
            boolean comp = Boolean.parseBoolean(parts[5]);
            LocalDate created = LocalDate.parse(parts[6]);
            return new Task(id, title, desc, freq, pts, comp, created);
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


