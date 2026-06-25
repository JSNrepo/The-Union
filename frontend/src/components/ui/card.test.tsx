import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardAction,
  CardContent,
  CardFooter,
} from "./card";

describe("Card Components", () => {
  it("renders Card with default size", () => {
    const { container } = render(<Card>Card Content</Card>);
    expect(container.firstChild).toHaveClass("group/card flex flex-col");
    expect(container.firstChild).toHaveAttribute("data-slot", "card");
    expect(container.firstChild).toHaveAttribute("data-size", "default");
  });

  it("renders Card with small size", () => {
    const { container } = render(<Card size="sm">Small Card</Card>);
    expect(container.firstChild).toHaveAttribute("data-size", "sm");
  });

  it("renders CardHeader", () => {
    const { container } = render(<CardHeader>Header</CardHeader>);
    expect(container.firstChild).toHaveAttribute("data-slot", "card-header");
  });

  it("renders CardTitle", () => {
    const { container } = render(<CardTitle>Title</CardTitle>);
    expect(container.firstChild).toHaveAttribute("data-slot", "card-title");
  });

  it("renders CardDescription", () => {
    const { container } = render(<CardDescription>Description</CardDescription>);
    expect(container.firstChild).toHaveAttribute("data-slot", "card-description");
  });

  it("renders CardAction", () => {
    const { container } = render(<CardAction>Action</CardAction>);
    expect(container.firstChild).toHaveAttribute("data-slot", "card-action");
  });

  it("renders CardContent", () => {
    const { container } = render(<CardContent>Content</CardContent>);
    expect(container.firstChild).toHaveAttribute("data-slot", "card-content");
  });

  it("renders CardFooter", () => {
    const { container } = render(<CardFooter>Footer</CardFooter>);
    expect(container.firstChild).toHaveAttribute("data-slot", "card-footer");
  });

  it("merges custom classNames", () => {
    const { container } = render(<Card className="custom-class" />);
    expect(container.firstChild).toHaveClass("custom-class");
  });
});
