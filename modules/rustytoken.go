//go:build rusty_token
// +build rusty_token

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
)

var (
	name           = "rustyTokenAnalyzer"
	description    = "Analyzes JSON Web Tokens (JWTs) using rusty_token"
	author         = "Your Name"
	category       = "Web"
	installCommand = "cargo install rusty_token" // Placeholder for future availability
	dependencies   = []string{"rusty_token"}
	parameters     = []map[string]interface{}{
		{"name": "jwt", "description": "JWT to analyze", "required": true, "default": ""},
		{"name": "format", "description": "Output format (html, json), defaults to text if not provided", "required": false, "default": "text"},
	}
)

func main() {
	metadata := flag.Bool("metadata", false, "Output metadata as JSON")
	var paramsJSON string
	flag.StringVar(&paramsJSON, "params", "", "JSON string containing module parameters")
	flag.Parse()

	if *metadata {
		meta := map[string]interface{}{
			"name":            name,
			"description":     description,
			"author":          author,
			"category":        category,
			"parameters":      parameters,
			"dependencies":    dependencies,
			"install_command": installCommand,
		}
		metaJSON, _ := json.Marshal(meta)
		fmt.Println(string(metaJSON))
		return
	}

	var params struct {
		JWT    string `json:"jwt"`
		Format string `json:"format"`
	}
	if err := json.Unmarshal([]byte(paramsJSON), &params); err != nil {
		fmt.Printf("{\"error\": \"Failed to parse parameters: %s\"}\n", err)
		os.Exit(1)
	}

	// Build the rusty_token command
	cmdArgs := []string{params.JWT}

	// Add format if specified
	if params.Format != "" {
		cmdArgs = append(cmdArgs, "--format", params.Format)
	}

	// Execute the rusty_token command
	cmd := exec.Command("rusty_token", cmdArgs...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("{\"error\": \"Failed to execute rusty_token: %s\"}\n", err)
		os.Exit(1)
	}

	result := struct {
		Output string `json:"output"`
	}{
		Output: string(output),
	}
	resultJSON, _ := json.Marshal(result)
	fmt.Println(string(resultJSON))
}
