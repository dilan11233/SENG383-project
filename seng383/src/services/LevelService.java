package services;

import models.User;

public class LevelService {
    private static final int[] LEVEL_THRESHOLDS = {0, 50, 120, 200, 300, 450, 600};

    public void updateLevel(User user) {
        int points = user.getPoints();
        int newLevel = 1;
        for (int i = 0; i < LEVEL_THRESHOLDS.length; i++) {
            if (points >= LEVEL_THRESHOLDS[i]) {
                newLevel = i + 1;
            }
        }
        user.setLevel(newLevel);
    }
}


