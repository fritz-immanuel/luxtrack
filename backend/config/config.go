// backend/config/config.go
package config

import (
	"log"
	"os"
	"strconv"
	"sync"

	"github.com/joho/godotenv"
)

type Config struct {
	AppName   string
	AppEnv    string
	AppPort   string
	DBHost    string
	DBPort    int
	DBUser    string
	DBPass    string
	DBName    string
	DebugLog  bool
	JwtSecret string
}

var (
	cfg  *Config
	once sync.Once
)

func load() *Config {
	_ = godotenv.Load("backend/.env")

	dbPort, err := strconv.Atoi(getEnv("DB_PORT", "5432"))
	if err != nil {
		log.Fatal("❌ Invalid DB_PORT, must be integer")
	}

	return &Config{
		AppName:   getEnv("APP_NAME", "LuxTrack"),
		AppEnv:    getEnv("APP_ENV", "development"),
		AppPort:   getEnv("APP_PORT", "8080"),
		DBHost:    getEnv("DB_HOST", "localhost"),
		DBPort:    dbPort,
		DBUser:    getEnv("DB_USER", "postgres"),
		DBPass:    getEnv("DB_PASS", ""),
		DBName:    getEnv("DB_NAME", "luxtrack"),
		DebugLog:  getEnv("DEBUG_LOG", "false") == "true",
		JwtSecret: getEnv("JWT_SECRET", ""),
	}
}

func getEnv(key, fallback string) string {
	val := os.Getenv(key)
	if val == "" {
		return fallback
	}
	return val
}

func Get() *Config {
	once.Do(func() {
		cfg = load()
	})
	return cfg
}

// LoadConfig returns a fresh load (used in main)
func LoadConfig() (*Config, error) {
	return Get(), nil
}
