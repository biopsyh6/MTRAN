package product

import "fmt"

type Product struct {
	Name     string
	Price    float64
	Quantity int
}

func (p Product) Info() {
	fmt.Printf("Товар: %s | Цена: %.2f | Количество: %d\n", p.Name, p.Price, p.Quantity)
	fmt.Print(`func (p Product) Info() {
	fmt.Printf("Товар: %s | Цена: %.2f | Количество: %d\n", p.Name, p.Price, p.Quantity)
	fmt.Print("dasdas")
}`)
}
