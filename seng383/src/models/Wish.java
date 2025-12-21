package models;

import java.util.UUID;

public class Wish {
    private final String id;
    private String description;
    private int costPoints;
    private boolean approved;

    public Wish(String id, String description, int costPoints, boolean approved) {
        this.id = id;
        this.description = description;
        this.costPoints = costPoints;
        this.approved = approved;
    }

    public Wish(String description, int costPoints) {
        this(UUID.randomUUID().toString(), description, costPoints, false);
    }

    public String getId() {
        return id;
    }

    public String getDescription() {
        return description;
    }

    public int getCostPoints() {
        return costPoints;
    }

    public boolean isApproved() {
        return approved;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public void setCostPoints(int costPoints) {
        this.costPoints = costPoints;
    }

    public void setApproved(boolean approved) {
        this.approved = approved;
    }

    public String toStorageString() {
        return String.join("|",
                id,
                escape(description),
                String.valueOf(costPoints),
                String.valueOf(approved));
    }

    public static Wish fromStorageString(String line) {
        try {
            String[] parts = line.split("\\|", -1);
            if (parts.length < 4) {
                return null;
            }
            String id = parts[0];
            String desc = unescape(parts[1]);
            int cost = Integer.parseInt(parts[2]);
            boolean approved = Boolean.parseBoolean(parts[3]);
            return new Wish(id, desc, cost, approved);
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


