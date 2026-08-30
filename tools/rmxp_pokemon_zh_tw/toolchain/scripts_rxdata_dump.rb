# scripts_rxdata_dump.rb
# Usage from the game root:
#   ruby scripts_rxdata_dump.rb Data/Scripts.rxdata dumped_scripts
require "zlib"
src = ARGV[0] || "Data/Scripts.rxdata"
out = ARGV[1] || "dumped_scripts"
Dir.mkdir(out) unless Dir.exist?(out)
scripts = Marshal.load(File.binread(src))
scripts.each_with_index do |entry, idx|
  id, name, compressed = entry
  safe = (name || "unnamed").gsub(/[^\p{L}\p{N}_\-. ]/u, "_")
  code = Zlib::Inflate.inflate(compressed)
  File.binwrite(File.join(out, "%04d_%s.rb" % [idx, safe]), code)
end
puts "Dumped #{scripts.length} scripts to #{out}"
