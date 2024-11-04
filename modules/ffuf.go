//go:build ffuf
// +build ffuf

package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
)

var (
	name           = "ffufFuzzer"
	description    = "Performs HTTP fuzzing using FFUF with modular fuzzing points"
	author         = "Your Name"
	category       = "Web"
	installCommand = "sudo apt install ffuf"
	dependencies   = []string{"ffuf"}
	parameters     = []map[string]interface{}{
		{"name": "target", "description": "Base target URL", "required": true, "default": ""},
		{"name": "subdomain", "description": "Subdomain to fuzz, replacing SUBDOMAIN_FUZZ", "required": false, "default": ""},
		{"name": "path", "description": "Path to fuzz, replacing PATH_FUZZ", "required": false, "default": ""},
		{"name": "query", "description": "Query parameter to fuzz, replacing QUERY_FUZZ", "required": false, "default": ""},
		{"name": "header", "description": "Header to fuzz, replacing HEADER_FUZZ", "required": false, "default": ""},
		{"name": "wordlist", "description": "Path to wordlist for fuzzing", "required": true, "default": ""},
		{"name": "options", "description": "Additional FFUF options", "required": false, "default": ""},
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
		Target    string `json:"target"`
		Subdomain string `json:"subdomain"`
		Path      string `json:"path"`
		Query     string `json:"query"`
		Header    string `json:"header"`
		Wordlist  string `json:"wordlist"`
		Options   string `json:"options"`
	}
	if err := json.Unmarshal([]byte(paramsJSON), &params); err != nil {
		fmt.Printf("{\"error\": \"Failed to parse parameters: %s\"}\n", err)
		os.Exit(1)
	}

	// Construct the base URL
	baseURL := params.Target

	// Add fuzz points to the base URL based on the specified parameters
	if params.Subdomain != "" {
		baseURL = fmt.Sprintf("http://%s.%s", params.Subdomain, baseURL)
	}
	if params.Path != "" {
		baseURL = fmt.Sprintf("%s/%s", baseURL, params.Path)
	}
	if params.Query != "" {
		baseURL = fmt.Sprintf("%s?%s", baseURL, params.Query)
	}

	// Build the FFUF command with modular fuzzing points
	cmdArgs := []string{"-u", baseURL, "-w", params.Wordlist}

	// Add headers for fuzzing if specified
	if params.Header != "" {
		cmdArgs = append(cmdArgs, "-H", params.Header)
	}

	// Include any additional FFUF options provided by the user
	if params.Options != "" {
		cmdArgs = append(cmdArgs, params.Options)
	}

	// Execute the FFUF command
	cmd := exec.Command("ffuf", cmdArgs...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("{\"error\": \"Failed to execute ffuf: %s\"}\n", err)
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
