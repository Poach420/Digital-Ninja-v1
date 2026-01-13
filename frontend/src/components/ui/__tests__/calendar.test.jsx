import { render, screen } from "@testing-library/react";
import { Calendar } from "../calendar";

describe("Calendar", () => {
    it("renders navigation controls", () => {
        render(<Calendar />);
        expect(
            screen.getByRole("button", { name: /previous month/i })
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: /next month/i })
        ).toBeInTheDocument();
    });
});
