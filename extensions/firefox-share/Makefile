xpcshell-tests:
	python -u $(MOZILLA)/config/pythonpath.py \
	       -I $(MOZILLA)/build \
	       -I $(MOZILLA)/testing/xpcshell \
	       $(MOZILLA)/testing/xpcshell/runxpcshelltests.py \
	       --symbols-path=$(MOZ_OBJDIR)/dist/crashreporter-symbols \
	       \
	       $(MOZ_OBJDIR)/dist/bin/xpcshell \
	       tests/unit

check-interactive:
	python -u $(MOZILLA)/config/pythonpath.py \
	       -I $(MOZILLA)/build \
	       -I $(MOZILLA)/testing/xpcshell \
	       $(MOZILLA)/testing/xpcshell/runxpcshelltests.py \
	         --symbols-path=$(MOZ_OBJDIR)/dist/crashreporter-symbols \
	         --test-path=$(SOLO_FILE) \
	         --profile-name=firefox \
	         --interactive \
	         --verbose \
	       \
	       $(MOZ_OBJDIR)/dist/bin/xpcshell \
	       tests/unit

check-one:
	python -u $(MOZILLA)/config/pythonpath.py \
	       -I $(MOZILLA)/build \
	       -I $(MOZILLA)/testing/xpcshell \
	       $(MOZILLA)/testing/xpcshell/runxpcshelltests.py \
	       --symbols-path=$(MOZ_OBJDIR)/dist/crashreporter-symbols \
           --test-path=$(SOLO_FILE) \
           --profile-name=firefox \
           --verbose \
	       \
	       $(MOZ_OBJDIR)/dist/bin/xpcshell \
	       tests/unit
