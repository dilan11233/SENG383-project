package services;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

import models.User;
import models.Wish;
import repository.FileRepository;
import utils.ErrorHandler;

public class WishService {
    private final FileRepository repo;
    private List<Wish> wishes;

    public WishService(FileRepository repo) {
        this.repo = repo;
        load();
    }

    private void load() {
        this.wishes = repo.readAll("Wishes.txt", Wish::fromStorageString);
        this.wishes.sort(Comparator.comparing(Wish::getDescription));
    }

    private void save() {
        repo.writeAll("Wishes.txt", wishes, Wish::toStorageString);
    }

    public List<Wish> getAll() {
        return new ArrayList<>(wishes);
    }

    public void addWish(Wish wish) {
        wishes.add(wish);
        save();
    }

    public boolean approveWish(String wishId, User user) {
        for (Wish wish : wishes) {
            if (wish.getId().equals(wishId) && !wish.isApproved()) {
                if (user.getPoints() >= wish.getCostPoints()) {
                    user.addPoints(-wish.getCostPoints());
                    wish.setApproved(true);
                    save();
                    return true;
                } else {
                    ErrorHandler.show("Not enough points to approve wish.");
                    return false;
                }
            }
        }
        ErrorHandler.log("Wish not found or already approved: " + wishId);
        return false;
    }
}


