Vagrant.configure("2") do |config|
  config.vm.define "stage" do |stage|
    stage.vm.box = "fedora/28-atomic-host"
    stage.vm.box_version = "28.20181007.0"

  config.vm.provider "libvirt" do |lv|
    lv.driver = "qemu"
    lv.memory = 1024
    lv.cpus   = 2
    end
  end
end
