//go:build nikto
// +build nikto

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
)

var (
	name           = "niktoScan"
	description    = "Performs a vulnerability scan using Nikto with configurable options"
	author         = "Your Name"
	category       = "Web"
	installCommand = "sudo apt install nikto"
	dependencies   = []string{"nikto"}
	parameters     = []map[string]interface{}{
		{"name": "url", "description": "Target URL to scan", "required": true, "default": ""},
		{"name": "timeout", "description": "Request timeout in seconds", "required": false, "default": "10"},
		{"name": "plugins", "description": "Comma-separated list of plugins to use", "required": false, "default": ""},
		{"name": "user_agent", "description": "Custom User-Agent string", "required": false, "default": ""},
		{"name": "proxy", "description": "Proxy URL (e.g., http://localhost:8080)", "required": false, "default": ""},
		{"name": "ssl", "description": "Force SSL on/off (true/false)", "required": false, "default": "false"},
		{"name": "options", "description": "Additional Nikto options", "required": false, "default": ""},
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
		URL       string `json:"url"`
		Timeout   string `json:"timeout"`
		Plugins   string `json:"plugins"`
		UserAgent string `json:"user_agent"`
		Proxy     string `json:"proxy"`
		SSL       string `json:"ssl"`
		Options   string `json:"options"`
	}
	if err := json.Unmarshal([]byte(paramsJSON), &params); err != nil {
		fmt.Printf("{\"error\": \"Failed to parse parameters: %s\"}\n", err)
		os.Exit(1)
	}

	// Build the Nikto command
	cmdArgs := []string{"-h", params.URL}

	// Add optional parameters based on user input
	if params.Timeout != "" {
		cmdArgs = append(cmdArgs, "-timeout", params.Timeout)
	}
	if params.Plugins != "" {
		cmdArgs = append(cmdArgs, "-Plugins", params.Plugins)
	}
	if params.UserAgent != "" {
		cmdArgs = append(cmdArgs, "-useragent", params.UserAgent)
	}
	if params.Proxy != "" {
		cmdArgs = append(cmdArgs, "-useproxy", params.Proxy)
	}
	if params.SSL == "true" {
		cmdArgs = append(cmdArgs, "-ssl")
	}

	// Include additional options provided by the user
	if params.Options != "" {
		cmdArgs = append(cmdArgs, params.Options)
	}

	// Execute the Nikto command
	cmd := exec.Command("nikto", cmdArgs...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("{\"error\": \"Failed to execute nikto: %s\"}\n", err)
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
