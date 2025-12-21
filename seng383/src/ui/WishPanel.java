package ui;

import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.util.List;
import java.util.function.Consumer;

import javax.swing.DefaultListModel;
import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextField;

import models.Wish;
import utils.Validators;

public class WishPanel extends JPanel {
    private final DefaultListModel<Wish> model = new DefaultListModel<>();
    private final JList<Wish> list = new JList<>(model);

    public WishPanel(Consumer<Wish> onAddWish, Consumer<String> onApproveWish) {
        setLayout(new BorderLayout());

        JPanel top = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JTextField descField = new JTextField(12);
        JTextField costField = new JTextField(5);
        JButton addBtn = new JButton("Add Wish");

        top.add(new JLabel("Wish"));
        top.add(descField);
        top.add(new JLabel("Cost"));
        top.add(costField);
        top.add(addBtn);

        add(top, BorderLayout.NORTH);
        add(new JScrollPane(list), BorderLayout.CENTER);

        JButton approveBtn = new JButton("Approve Selected");
        JPanel bottom = new JPanel(new FlowLayout(FlowLayout.LEFT));
        bottom.add(approveBtn);
        add(bottom, BorderLayout.SOUTH);

        addBtn.addActionListener(e -> {
            String desc = descField.getText();
            int cost = Validators.parsePositiveInt(costField.getText(), 10);
            onAddWish.accept(new Wish(desc, cost));
            descField.setText("");
            costField.setText("");
        });

        approveBtn.addActionListener(e -> {
            Wish selected = list.getSelectedValue();
            if (selected != null) {
                onApproveWish.accept(selected.getId());
            }
        });

        list.setCellRenderer((list, value, index, isSelected, cellHasFocus) -> {
            JLabel label = new JLabel(value.getDescription() + " - cost " + value.getCostPoints() +
                    (value.isApproved() ? " [approved]" : ""));
            if (isSelected) {
                label.setOpaque(true);
                label.setBackground(list.getSelectionBackground());
                label.setForeground(list.getSelectionForeground());
            }
            return label;
        });
    }

    public void setWishes(List<Wish> wishes) {
        model.clear();
        for (Wish w : wishes) {
            model.addElement(w);
        }
    }
}


