package store;
import ("test_code/product";
 		"fmt";)

type Store struct {
	products map[string]product.Product;
};
///////////////////////////
func NewStore() Store {
	return Store{products: make(map[string]product.Product)}
}

func (s Store) AddProduct(name string, price float64, quantity int) Store {
	s.products[name] = product.Product{Name: name, Price: price, Quantity: quantity}
	return s
}

// func (s Store) ListProducts() {
// 	for _, product := range s.products {
// 		product.Info()
// 	}
// }

// func (s Store) BuyProduct(name string, quantity int) (Store, bool) {
// 	product, exists := s.products[name]

// 	if !exists {
// 		fmt.Println("Товар не найден!")
// 		return s, false
// 	}

// 	purchasedQuantities := make([]int, 0)
// 	switch{
// 		case product.Quantity < quantity:
// 			fmt.Println("Недостаточно товара в наличии!")
// 			return s, false

// 		case product.Quantity == quantity:
// 			fmt.Println("Вы купили весь товар!")
		
// 		default:
// 			product.Quantity -= quantity
// 			fmt.Printf("Вы купили %d шт. товара '%s'. Осталось: %d\n", quantity, name, product.Quantity)
// 	}
// 	purchasedQuantities = append(purchasedQuantities, quantity)
// 	///////////////////////
// 	if quantity > 1 {
// 		product.Quantity >>= 1
// 		fmt.Printf("Количество после сдвига: %d\n", product.Quantity)
// 	} else {
// 		product.Quantity -= quantity
// 	}
// 	////////////////////////
// 	s.products[name] = product
	

// 	fmt.Printf("Купленные количества: %v\n", purchasedQuantities)

// 	return s, true
// }